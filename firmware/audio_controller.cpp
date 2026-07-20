#include "audio_controller.h"



#define SAMPLE_RATE 16000
#define SAMPLE_BITS I2S_DATA_BIT_WIDTH_16BIT
#define BUFFER_SIZE   1024




using namespace websockets;



AudioController::AudioController(int ws, int sck, int sd, int bclk, int lrc, int din, const char* host, uint16_t port, bool debug){
  this->ws=ws; this->sck = sck; this->sd = sd; this->host = host; this->port = port;
  this->bclk=bclk; this->lrc=lrc; this->din=din;

  recording = false;
  ws_url = String("ws://") + host + ":" + String(port);
  this->debug = debug;
}



void AudioController::setup(){
  
  setupMicI2S();
  setupSpeakerI2S();

  //connect callbacks to websocket
  client.onMessage([this](WebsocketsMessage message){
    onMessageCallback(message);
  });

  client.onEvent([this](WebsocketsEvent event, String data){
    onEventsCallback(event, data);
  });

  while (!client.available()){
    client.connect(ws_url);
    delay(50);
  }

  Serial.print("Audio Capture Websocket connected -> ");
  Serial.println(host);

}


// Microphone constant stream


void AudioController::send(){

  const int buffer_samples = 256;
  uint16_t i2s_buffer[buffer_samples];
  size_t bytes_read = 0;

  i2s_channel_read(rx_handle, &i2s_buffer, buffer_samples * sizeof(uint16_t), &bytes_read, portMAX_DELAY);


  if(client.available()){

    static uint32_t debugCounter = 0;
    if(debugCounter++ % 50 == 0 && debug){
      Serial.print("Sample[0]: ");
      Serial.println(i2s_buffer[0]);
    }

    client.sendBinary((const char*)i2s_buffer, bytes_read);
  }
  else{
    Serial.print("Reconnecting...");

    while(!client.available()){
      client.connect(ws_url);
      Serial.print(".");
    }

    Serial.println();
    
    Serial.println("Successfully reconnected to audio websocket.");
  }
}

void AudioController::play(){
  client.send("send_audio");
}

//speaker loop check to play audio


void AudioController::loop() {
  if (currentState != PLAYING || audioDataSize == 0) return;
  
  size_t bytesWritten;
  size_t bytesToWrite = min((size_t)BUFFER_SIZE * 2, (size_t)audioDataSize);
  
  esp_err_t result = i2s_channel_write(tx_handle, audioData, bytesToWrite, &bytesWritten, 100);
  
  if (result == ESP_OK && bytesWritten > 0) {
    // Shift remaining data
    audioDataSize -= bytesWritten;
    if (audioDataSize > 0) {
      memmove(audioData, audioData + bytesWritten, audioDataSize);
    } 
    else {
      Serial.println("Playback finished!");
      currentState = IDLE;
    }
  }
}


// websocket callback, message handling


void AudioController::onMessageCallback(WebsocketsMessage message) 
{
  
  if (message.isText()) {
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, message.data());
    
    String type = doc["type"];
    
    
  } 
  else if (message.isBinary()) {

    // Receiving audio data back from server
    Serial.println("Receiving audio data from server...");
    
    size_t dataSize = message.length();
    if (dataSize <= MAX_AUDIO_BUFFER) {
      memcpy(audioData, message.c_str(), dataSize);
      audioDataSize = dataSize;
      currentState = PLAYING;
      Serial.println("Starting playback...");
    } else {
      Serial.println("Error: Audio data too large");
    }
  }
}

void AudioController::onEventsCallback(WebsocketsEvent event, String data) 
{
  if (event == WebsocketsEvent::ConnectionOpened) {
    Serial.println("WebSocket Connected!");
  } 
  else if (event == WebsocketsEvent::ConnectionClosed) {
    Serial.println("WebSocket Disconnected!");
  } 
  else if (event == WebsocketsEvent::GotPing) {
    Serial.println("Got ping from server!");
  } 
  else if (event == WebsocketsEvent::GotPong) {
    Serial.println("Got pong from server!");
  }
}



// I2S Setup and Config


void AudioController::setupMicI2S(){
  i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
  chan_cfg.dma_desc_num = 8;
  chan_cfg.dma_frame_num = 512;
  i2s_new_channel(&chan_cfg, NULL, &rx_handle);

  i2s_std_config_t std_cfg = {
    .clk_cfg  = I2S_STD_CLK_DEFAULT_CONFIG(SAMPLE_RATE),
    .slot_cfg = I2S_STD_MSB_SLOT_DEFAULT_CONFIG(SAMPLE_BITS, I2S_SLOT_MODE_MONO),
    .gpio_cfg = {
      .mclk = I2S_GPIO_UNUSED,
      .bclk = (gpio_num_t)sck,
      .ws   = (gpio_num_t)ws,
      .dout = I2S_GPIO_UNUSED,
      .din  = (gpio_num_t)sd,
      .invert_flags = {
        .mclk_inv = false,
        .bclk_inv = false,
        .ws_inv   = false,
      },
    },
  };
  std_cfg.slot_cfg.slot_mask = I2S_STD_SLOT_LEFT;

  i2s_channel_init_std_mode(rx_handle, &std_cfg);
  i2s_channel_enable(rx_handle);
}

void AudioController::setupSpeakerI2S(){
  i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_1, I2S_ROLE_MASTER);
  chan_cfg.dma_desc_num = 4;
  chan_cfg.dma_frame_num = BUFFER_SIZE;
  i2s_new_channel(&chan_cfg, &tx_handle, NULL);

  i2s_std_config_t std_cfg = {
    .clk_cfg  = I2S_STD_CLK_DEFAULT_CONFIG(SAMPLE_RATE),
    .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(SAMPLE_BITS, I2S_SLOT_MODE_MONO),
    .gpio_cfg = {
      .mclk = I2S_GPIO_UNUSED,
      .bclk = (gpio_num_t)bclk,
      .ws   = (gpio_num_t)lrc,
      .dout = (gpio_num_t)din,
      .din  = I2S_GPIO_UNUSED,
      .invert_flags = {
        .mclk_inv = false,
        .bclk_inv = false,
        .ws_inv   = false,
      },
    },
  };
  std_cfg.slot_cfg.slot_mask = I2S_STD_SLOT_LEFT;

  i2s_channel_init_std_mode(tx_handle, &std_cfg);
  i2s_channel_enable(tx_handle);
}