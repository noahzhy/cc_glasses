#ifndef IR_GLASSES_EVT_E6_INTERFACE_H
#define IR_GLASSES_EVT_E6_INTERFACE_H
#include <stdint.h>
#include <stddef.h>
/* Interface only: this is not a runnable firmware implementation.
 * Serialize each integer explicitly in little-endian order. */
#define EVT_E6_PCLK_HZ 48000000u
#define EVT_E6_SPI_SCLK_HZ 3000000u
#define EVT_E6_SLOT_US 1250u
#define EVT_E6_TIM1_ACTIVE_US 1000u
#define EVT_E6_DMA_CHANNELS_REQUIRED 3u
#define EVT_E6_PROTOCOL_VERSION 0xE6u
#define EVT_E6_LED_COUNT 16u
#define EVT_E6_PD_COUNT 16u
#define EVT_E6_PD_DISABLED 0u
#define EVT_E6_SAMPLE_WIRE_BYTES 40u
#define EVT_E6_VALID_A (1u << 0)
#define EVT_E6_VALID_B (1u << 1)
enum evt_e6_fault {
    EVT_E6_FAULT_SPI = 1u << 0,
    EVT_E6_FAULT_OVERRUN = 1u << 1,
    EVT_E6_FAULT_CONFIG = 1u << 2,
    EVT_E6_FAULT_SATURATION = 1u << 3,
    EVT_E6_FAULT_UNSETTLED = 1u << 4,
    EVT_E6_FAULT_PIPELINE = 1u << 5
};
typedef struct {
    uint8_t led_id;       /* 1..16; D1..D16 */
    uint8_t valid_mask;   /* 3: both adjacent PDs; 1: odd only; 2: even only */
} evt_e6_slot_config;
typedef struct {
    uint8_t pd_a_id, pd_b_id, mux_a_address, mux_b_address;
} evt_e6_pd_pair;
/* Index is LED_ID - 1. Invalid LED IDs must be rejected before indexing. */
static const evt_e6_pd_pair evt_e6_adjacent_pd[EVT_E6_LED_COUNT] = {
    {1, 2, 0, 0}, /* D1 */
    {3, 2, 1, 0}, /* D2 */
    {3, 4, 1, 1}, /* D3 */
    {5, 4, 2, 1}, /* D4 */
    {5, 6, 2, 2}, /* D5 */
    {7, 6, 3, 2}, /* D6 */
    {7, 8, 3, 3}, /* D7 */
    {1, 8, 0, 3}, /* D8 */
    {9, 10, 4, 4}, /* D9 */
    {11, 10, 5, 4}, /* D10 */
    {11, 12, 5, 5}, /* D11 */
    {13, 12, 6, 5}, /* D12 */
    {13, 14, 6, 6}, /* D13 */
    {15, 14, 7, 6}, /* D14 */
    {15, 16, 7, 7}, /* D15 */
    {9, 16, 4, 7}, /* D16 */
};
typedef struct {
    uint8_t protocol_version; /* offset 0: 0xE6 */
    uint8_t valid_mask;       /* offset 1 */
    uint16_t fault_flags;     /* offset 2 */
    uint32_t frame_seq;       /* offset 4 */
    uint16_t slot_seq;        /* offset 8: 0..15 */
    uint8_t led_id;           /* offset 10 */
    uint8_t pd_a_id;           /* offset 11: odd PD, or 0 when invalid */
    uint8_t pd_b_id;           /* offset 12: even PD, or 0 when invalid */
    uint8_t reserved[3];      /* offset 13: zero */
    uint32_t sample_seq;      /* offset 16: one increment per paired slot result */
    uint32_t light_time_us;   /* offset 20: actual light-sample edge, modulo 2^32 */
    uint16_t dark_a;          /* offset 24 */
    uint16_t dark_b;          /* offset 26 */
    uint16_t light_a;         /* offset 28 */
    uint16_t light_b;         /* offset 30 */
    int32_t delta_a;          /* offset 32 */
    int32_t delta_b;          /* offset 36 */
} evt_e6_sample;
#if defined(__cplusplus)
static_assert(sizeof(evt_e6_sample) == EVT_E6_SAMPLE_WIRE_BYTES, "E6 sample layout");
static_assert(offsetof(evt_e6_sample, dark_a) == 24, "E6 sample offsets");
#elif defined(__STDC_VERSION__) && __STDC_VERSION__ >= 201112L
_Static_assert(sizeof(evt_e6_sample) == EVT_E6_SAMPLE_WIRE_BYTES, "E6 sample layout");
_Static_assert(offsetof(evt_e6_sample, dark_a) == 24, "E6 sample offsets");
#endif
#endif
