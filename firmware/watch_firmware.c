/*
 * HUME LED Watch firmware skeleton  --  ATtiny3217 (tinyAVR 1-series) @ 20 MHz
 * ---------------------------------------------------------------------------
 * Architecture (current): the MCU does NOT drive LEDs directly. A Lumissil
 * IS31FL3743A matrix driver handles all multiplexing + 8-bit hardware PWM per
 * LED. The MCU just: sleep -> wake -> read time -> write a brightness frame
 * over I2C -> sleep. No scan loop, no Charlieplex, no per-LED timing.
 *
 * On-demand display: power-down sleep, wake on accel (wrist-raise) or button.
 * Timekeeping offloaded to RV-3028 RTC over I2C.
 *
 * Display: 132 LEDs (60 second + 60 minute + 12 hour). GMT dropped.
 * Each LED maps to a (SW,CS) cell in the driver's 18x11 matrix -> a PWM
 * register address. See pcb/dial/dial_matrix.csv for the LED->(SW,CS) map.
 *
 * STRUCTURE / REFERENCE, not a drop-in binary. The TWI(I2C) driver, the RTC
 * register reads, and exact IS31FL3743A page/register addresses are stubbed or
 * simplified where they'd be device/library-specific.
 *
 * Build: modern ATtiny toolchain (megaTinyCore-style), -mmcu=attiny3217,
 *        programmed via UPDI.
 */

#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <stdint.h>

/* ---------- I2C addresses (7-bit) ---------- */
#define ADDR_DRIVER0   0x20   /* IS31FL3743A, ADDR strap -> base address */
#define ADDR_RTC       0x52   /* RV-3028                                  */
#define ADDR_ACCEL     0x19   /* LIS2DH12                                 */

/* ---------- Pin map (ATtiny3217, only ~7 IO used) ----------
 * I2C : PB0 SCL, PB1 SDA (TWI)
 * SDB : PA4 -> driver shutdown/enable (high = on)
 * INTB: PA5 <- driver fault (optional)
 * ACC : PA6 <- accelerometer interrupt (wrist-raise)
 * BTN : PA7 <- crown button
 * STAT: PC0 <- charger status (optional)
 */
#define SDB_PORT  PORTA
#define SDB_PIN   PIN4_bm

/* ---------- Display model ----------
 * 132-byte framebuffer indexed by LED number (D1..D132 -> 0..131), matching
 * dial_matrix.csv order. led_to_reg[] converts LED index to the driver PWM
 * register offset for its (SW,CS) cell.
 */
#define N_LEDS    132
#define N_SEC     60
#define N_MIN     60
#define N_HOUR    12
#define SEC_BASE  0
#define MIN_BASE  60
#define HOUR_BASE 120

static uint8_t framebuf[N_LEDS];
static uint8_t led_to_reg[N_LEDS];   /* (SW-1)*18 + (CS-1); identity stub below */

/* ============================================================ I2C (stubbed) */
static void i2c_init(void) { /* TWI master ~400kHz */ }
static void i2c_w8(uint8_t a, uint8_t r, uint8_t v) { (void)a;(void)r;(void)v; }
static uint8_t i2c_r8(uint8_t a, uint8_t r) { (void)a;(void)r; return 0; }

/* ============================================================ IS31FL3743A */
#define REG_COMMAND  0xFD
#define REG_UNLOCK   0xFE
#define UNLOCK_KEY   0xC5
#define PAGE_PWM     0x00
#define PAGE_SCALING 0x01
#define PAGE_CONFIG  0x02
#define CFG_REG      0x00      /* SSD bit: software shutdown */
#define GCC_REG      0x01      /* global current control */

static void drv_page(uint8_t a, uint8_t page) {
    i2c_w8(a, REG_UNLOCK, UNLOCK_KEY);
    i2c_w8(a, REG_COMMAND, page);
}
static void drv_init(uint8_t a) {
    drv_page(a, PAGE_CONFIG);
    i2c_w8(a, CFG_REG, 0x01);            /* normal operation */
    i2c_w8(a, GCC_REG, 0x40);            /* global current; tune brightness */
    drv_page(a, PAGE_SCALING);
    for (uint8_t r = 0; r < 198; r++) i2c_w8(a, r, 0xFF);  /* full scale */
}
static void drv_write_frame(uint8_t a) {
    drv_page(a, PAGE_PWM);
    for (uint8_t i = 0; i < N_LEDS; i++) i2c_w8(a, led_to_reg[i], framebuf[i]);
    /* real code: one auto-increment burst instead of 132 single writes */
}
static void drv_enable(uint8_t on) {
    if (on) SDB_PORT.OUTSET = SDB_PIN; else SDB_PORT.OUTCLR = SDB_PIN;
}

/* ============================================================ RTC */
typedef struct { uint8_t h, m, s; } wtime_t;
static uint8_t bcd2bin(uint8_t b) { return (b >> 4) * 10 + (b & 0x0F); }
static wtime_t rtc_read(void) {
    wtime_t t;
    t.s = bcd2bin(i2c_r8(ADDR_RTC, 0x00));
    t.m = bcd2bin(i2c_r8(ADDR_RTC, 0x01));
    t.h = bcd2bin(i2c_r8(ADDR_RTC, 0x02));
    return t;
}

/* ============================================================ Render
 * The driver architecture pays off here: smooth fades and the seconds sweep
 * are just brightness values; the driver PWMs them in hardware.
 */
static void clear_frame(void) { for (uint8_t i = 0; i < N_LEDS; i++) framebuf[i] = 0; }

static void render(wtime_t t, uint8_t subsec) {
    clear_frame();
    /* SECOND: cross-fade s -> s+1 by subsec phase (smooth glide) */
    uint8_t s0 = t.s % N_SEC, s1 = (s0 + 1) % N_SEC;
    framebuf[SEC_BASE + s0] = 255 - subsec;
    framebuf[SEC_BASE + s1] = subsec;
    /* MINUTE + HOUR: single lit pipe each (12h face) */
    framebuf[MIN_BASE + (t.m % N_MIN)] = 255;
    framebuf[HOUR_BASE + (t.h % N_HOUR)] = 255;
}

/* ============================================================ Wake */
static volatile uint8_t wake_flag = 0;
ISR(PORTA_PORT_vect) { PORTA.INTFLAGS = PORTA.INTFLAGS; wake_flag = 1; }

static void io_init(void) {
    SDB_PORT.DIRSET = SDB_PIN;
    drv_enable(0);                       /* driver off at boot */
    PORTA.DIRCLR = PIN6_bm | PIN7_bm;    /* accel INT + button inputs */
    PORTA.PIN6CTRL = PORT_PULLUPEN_bm | PORT_ISC_FALLING_gc;
    PORTA.PIN7CTRL = PORT_PULLUPEN_bm | PORT_ISC_FALLING_gc;
}

static void go_to_sleep(void) {
    set_sleep_mode(SLEEP_MODE_PWR_DOWN); /* ~1uA; RTC keeps time externally */
    sleep_enable(); sei(); sleep_cpu(); sleep_disable();
}

/* ============================================================ Session (~3s) */
#define SESSION_MS 3000
#define FRAME_MS   16            /* ~60 fps */
#define PHASE_STEP ((256 * FRAME_MS) / 1000)

static void display_session(void) {
    drv_enable(1);
    drv_init(ADDR_DRIVER0);
    wtime_t t = rtc_read();
    uint16_t elapsed = 0; uint8_t subsec = 0;
    while (elapsed < SESSION_MS) {
        render(t, subsec);
        drv_write_frame(ADDR_DRIVER0);
        uint8_t prev = subsec; subsec += PHASE_STEP;
        if (subsec < prev) t = rtc_read();   /* phase wrapped -> new second */
        for (volatile uint32_t d = 0; d < 8000; d++) { } /* use a timer IRL */
        elapsed += FRAME_MS;
    }
    clear_frame(); drv_write_frame(ADDR_DRIVER0);
    drv_enable(0);                          /* driver back to shutdown */
}

/* ============================================================ main */
int main(void) {
    io_init();
    i2c_init();
    for (uint8_t i = 0; i < N_LEDS; i++) led_to_reg[i] = i;  /* (SW,CS) map stub */
    for (;;) {
        go_to_sleep();
        if (wake_flag) { wake_flag = 0; display_session(); }
    }
}

/*
 * vs the old Charlieplex firmware (watch_firmware_charlieplex_STALE.c):
 *  - No 13-pin scan loop, no tristate ghost-prevention, no cp_table.
 *  - The seconds sweep is a cross-fade of two brightness bytes; the driver
 *    PWMs them in hardware. The old version faked PWM by time-slicing the scan.
 *  - Scaling to more LEDs = more driver chips on the same I2C bus; render() and
 *    the framebuffer just grow, structure unchanged.
 *  - Lowest power: driver in SDB shutdown + MCU power-down between glances;
 *    only the RV-3028 stays awake (~45nA).
 */
