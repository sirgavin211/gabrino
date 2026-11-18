#include "audio-controller.h"
#include "driver/i2s.h"
#include "esp_err.h"
#include "freertos/portmacro.h"
#include <Arduino.h>

const i2s_config_t config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = 16000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT, // L/R pin to GND
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .dma_buf_count = 4,
    .dma_buf_len = 1024,
};

const i2s_pin_config_t pin_config = {
    .bck_io_num = 26, // SCK
    .ws_io_num = 25,  // WS
    .data_out_num = -1,
    .data_in_num = 33, // SD
};

void Microphone::setup() {
  esp_err_t err;
  err = i2s_driver_install(I2S_NUM_0, &config, 0, NULL);
  if (err != ESP_OK) {
    Serial.printf("failed initializing mic: %s\n", esp_err_to_name(err));
    while (true)
      ;
  }
  err = i2s_set_pin(I2S_NUM_0, &pin_config);
  if (err != ESP_OK) {
    Serial.printf("failed initializing mic: %s\n", esp_err_to_name(err));
    while (true)
      ;
  }
}

Sample Microphone::read() {
  esp_err_t err;
  Sample sample;
  err = i2s_read(I2S_NUM_0, sample.buf, sizeof(sample.buf), &sample.bytes_read,
                 portMAX_DELAY);

  if (err != ESP_OK) {
    Serial.printf("Failed to read mic sample: %s\n", esp_err_to_name(err));
  }

  return sample;
}
