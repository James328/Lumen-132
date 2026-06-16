/*
 * LED Watch firmware skeleton  --  ATmega328P @ internal 8 MHz
 * On-demand display: power-down sleep, wake on accel (wrist-raise) or button.
 * Timekeeping offloaded to RV-3028 RTC over I2C. 156 LEDs Charlieplexed on 13 pins.
 *
 * This is a STRUCTURE / REFERENCE, not a drop-in binary. The LED lookup table
 * (cp_table) and the I2C/RTC driver are stubbed where they'd be device-specific.
 *
 * Build: avr-gcc, -mmcu=atmega328p. Fuses: internal 8MHz, BOD enabled.
 */

#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <util/delay.h>
#include <stdint.h>

/* ---------- Pin map (see pin-budget calc) ----------
 * Charlieplex CP0..CP12 spread across PB0-7, PC0-3, PD4.
 * We address them through a uniform table so the scan code stays generic.
 */
typedef struct { volatile uint8_t *ddr, *port; uint8_t bit; } cp_pin_t;

static const cp_pin_t CP[13] = {
    {&DDRB,&PORTB,0},{&DDRB,&PORTB,1},{&DDRB,&PORTB,2},{&DDRB,&PORTB,3},
    {&DDRB,&PORTB,4},{&DDRB,&PORTB,5},{&DDRB,&PORTB,6},{&DDRB,&PORTB,7},
    {&DDRC,&PORTC,0},{&DDRC,&PORTC,1},{&DDRC,&PORTC,2},{&DDRC,&PORTC,3},
    {&DDRD,&PORTD,4}
};

/* Each physical LED = (high_pin, low_pin). 156 entries.
 * Index scheme: 0..59 second, 60..119 minute, 120..131 hour, 132..155 GMT.
 * Filled at design time from the arc-clustered assignment. Stub shown.
 */
typedef struct { uint8_t hi, lo; } led_t;
static const led_t cp_table[156] = {
    /* {hi,lo} pairs -- generated from the Charlieplex arc assignment */
    {0,1},{1,0},{0,2},{2,0}, /* ... 152 more ... */
};

/* ---------- Charlieplex core ---------- */

/* All 13 pins to high-impedance input, no pullups. This is the OFF state
 * and the ghost-prevention guarantee: any pin not actively driven is hi-Z. */
static void cp_all_hiz(void) {
    for (uint8_t i = 0; i < 13; i++) {
        *CP[i].ddr  &= ~(1 << CP[i].bit);   /* input  */
        *CP[i].port &= ~(1 << CP[i].bit);   /* no pull-up */
    }
}

/* Light exactly one LED: drive hi pin HIGH, lo pin LOW, everything else hi-Z. */
static inline void cp_light(uint8_t led) {
    cp_all_hiz();
    uint8_t h = cp_table[led].hi, l = cp_table[led].lo;
    *CP[h].port |=  (1 << CP[h].bit);   /* HIGH first (source) */
    *CP[h].ddr  |=  (1 << CP[h].bit);
    *CP[l].port &= ~(1 << CP[l].bit);   /* LOW (sink) */
    *CP[l].ddr  |=  (1 << CP[l].bit);
}

/* ---------- Frame state (set on display entry, read by the scan ISR) ---------- */
static volatile uint8_t  led_hour, led_min, led_gmt;   /* indices into cp_table */
static volatile uint8_t  led_sec_a, led_sec_b;         /* the two seconds LEDs to cross-fade */
static volatile uint8_t  sec_mix;        /* 0..15: brightness weight of led_sec_b vs led_sec_a */
static volatile uint8_t  display_active; /* set while in display state */

/* PWM/scan bookkeeping */
static volatile uint8_t  pwm_phase;      /* 0..15 sub-slot within a frame */

/*
 * Timer2 ISR = the heartbeat. Fires fast enough to: visit all 13 rows AND
 * run 16 PWM sub-slots for the seconds cross-fade, ~70 frames/sec.
 * Strategy: each ISR tick lights ONE thing briefly. We cycle through the
 * four active LEDs; for the two seconds LEDs we gate their on-time by sec_mix
 * so the apparent dot glides between positions.
 */
ISR(TIMER2_COMPA_vect) {
    if (!display_active) { cp_all_hiz(); return; }

    /* Round-robin the 4 logical indicators across successive ticks.
     * hour, minute, gmt always full brightness; seconds split by sec_mix. */
    static uint8_t slot = 0;
    switch (slot) {
        case 0: cp_light(led_hour); break;
        case 1: cp_light(led_min);  break;
        case 2: cp_light(led_gmt);  break;
        case 3:
            /* seconds sweep: within this slot, give led_sec_a (16-mix) ticks
             * and led_sec_b (mix) ticks, using pwm_phase as the comparator. */
            if (pwm_phase < (16 - sec_mix)) cp_light(led_sec_a);
            else                            cp_light(led_sec_b);
            break;
    }
    slot = (slot + 1) & 0x03;
    if (slot == 0) pwm_phase = (pwm_phase + 1) & 0x0F;
}

/* ---------- Wake interrupts ---------- */
ISR(INT0_vect) { /* accel wrist-raise */ }   /* just wakes the core */
ISR(INT1_vect) { /* crown button      */ }

static void enter_sleep(void) {
    display_active = 0;
    cp_all_hiz();
    TIMSK2 &= ~(1 << OCIE2A);          /* stop scan timer */
    set_sleep_mode(SLEEP_MODE_PWR_DOWN);
    sleep_enable();
    sei();
    sleep_cpu();                       /* <-- sleeps here at ~1uA */
    sleep_disable();                   /* resumes here after an INT */
}

/* ---------- RTC (RV-3028) over I2C -- stubbed ---------- */
static void rtc_read(uint8_t *h, uint8_t *m, uint8_t *s) {
    /* i2c read BCD time registers, convert. Stub: */
    *h = 10; *m = 8; *s = 30;
}

/* Map a time field to its LED index using the ring assignment. */
static uint8_t idx_second(uint8_t s){ return 0   + s; }
static uint8_t idx_minute(uint8_t m){ return 60  + m; }
static uint8_t idx_hour  (uint8_t h){ return 120 + (h % 12); }
static uint8_t idx_gmt   (uint8_t h){ return 132 + (h % 24); }

/* ---------- Display state ---------- */
static void run_display(void) {
    uint8_t h, m, s;
    rtc_read(&h, &m, &s);

    led_hour = idx_hour(h);
    led_min  = idx_minute(m);
    led_gmt  = idx_gmt(h);

    display_active = 1;
    TCNT2 = 0;
    TIMSK2 |= (1 << OCIE2A);           /* start scan timer */

    /* ~3 seconds of display. During it, animate the seconds sweep by
     * updating led_sec_a/b and sec_mix from a sub-second counter. */
    for (uint16_t frame = 0; frame < 210; frame++) {
        /* fractional second 0..15 -> which two LEDs and the mix.
         * Here we derive sub-second from the frame counter for the sweep;
         * on entry align to RTC seconds, then interpolate. */
        uint8_t sub = (frame >> 1) & 0x0F;          /* 0..15 over ~0.45s */
        led_sec_a = idx_second(s % 60);
        led_sec_b = idx_second((s + 1) % 60);
        sec_mix   = sub;                            /* glide a -> b */
        if (sub == 15) { s = (s + 1) % 60; }
        _delay_ms(14);                              /* ~70 Hz frame pacing */
    }

    display_active = 0;
    TIMSK2 &= ~(1 << OCIE2A);
    cp_all_hiz();
}

/* ---------- Init ---------- */
static void init(void) {
    cp_all_hiz();

    /* External interrupts: falling edge on INT0 (accel) and INT1 (button) */
    EICRA = (1 << ISC01) | (1 << ISC11);   /* falling edge both */
    EIMSK = (1 << INT0)  | (1 << INT1);

    /* Timer2: CTC, prescale for ~ (4 indicators * 16 phases * 70Hz) tick rate.
     * tick ~ 70*4*16 = 4480 Hz -> period ~223us. At 8MHz/64 = 125kHz, OCR2A~28. */
    TCCR2A = (1 << WGM21);
    TCCR2B = (1 << CS22);                  /* /64 */
    OCR2A  = 28;

    /* I2C init, RV-3028 + LIS2DH12 config (wrist-raise INT) -- stubbed */
}

int main(void) {
    init();
    sei();
    for (;;) {
        enter_sleep();      /* wakes on accel or button INT */
        run_display();      /* show ~3s, sweep seconds */
        /* long-press detection would branch to set_time() here */
    }
}
