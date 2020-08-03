#include <MegunoLink.h>
#include <MovingAverageFilter.h>

#include <Filter.h>

MovingAverageFilter topAverageFilter(20);
MovingAverageFilter midAverageFilter(20);
MovingAverageFilter chainAverageFilter(15);

ExponentialFilter<float> top_filter(10, 8);
ExponentialFilter<float> mid_filter(10, 8);
ExponentialFilter<float> chain_filter(10, 7);

unsigned long startTime;
int fps = 600;
float scanZone = 13.5;

// testing constants
float SPEED = 730.0;

float top_left = 0;
float top_peak = 0;
float top_right = 0;

float mid_left = 0;
float mid_peak = 0;
float mid_right = 0;

float delta_left = 0;
float delta_top = 0;
float delta_right = 0;

float delta_yaw = 0;

float chain_interval = 0;
float chain_peak = 0;
float chain_left = 0;

float data_top[600];
float data_mid[600];
int index = 0;
//int reset = 0;

bool isReading = false;

int delta_count = 0;

void setup() {
  startTime - millis();
  Serial.begin(57600);

}
int d = 0;
int readChain(float dist) {
  // hit
  if (dist > 12.0 || dist < 5 ) {
    return 1;
  } else {
    return 2;
  }

}


void loop() {
  unsigned long curTime = millis();
  float volts, top, top1, mid, mid1, top_current, mid_current;
  float yawInterval = 0;
  bool yawstart = false;

  if (curTime > startTime + (1000 / fps)) {
    ////////////////////////////////////////////
    // former
    volts = analogRead(A0) * 0.0048828125;
    top = 13 * pow(volts, -1);

    volts = analogRead(A2) * 0.0048828125;
    mid = 13 * pow(volts, -1);

    ////////////////////////////////////////////
    // chain
    volts = analogRead(A5) * 0.0048828125;
    float chain = 13 * pow(volts, -1);

    float chain_now = chainAverageFilter.process(chain);

    if (!(isinf(chain_now))) {
      if (chain_now < 15.0) {
        if (chain_peak == 0 || chain_peak > chain_now) {
          chain_peak = chain_now;
        }
        isReadingChain = true;
      } else {
        if (isReadingChain) {
          int stat = readChain(chain_peak);

          if (stat != 0) {
            Serial.print("chain?dist=");
            Serial.print(chain_peak);
            Serial.print("&status=");
            Serial.println(stat);
            
          }

          chain_peak = 0;
          chain_left = 0;
          isReadingChain = false;
        }
      }
    }

    ////////////////////////////////////////////
    // former
    top1 = topAverageFilter.process(top);
    mid1 = topAverageFilter.process(mid);

    if (!(isinf(top1) || isinf(mid1) || mid1 > 20 || top1 > 20)) {
      top_filter.Filter(top1);
      mid_filter.Filter(mid1);

      top_current = top_filter.Current();
      mid_current = mid_filter.Current();

      if (top_current < 12 || mid_current < 12 ) {
        //TOP
        if (top_current < 12) {
          if (top_left == 0) {
            top_left = top_current;
            top_peak = top_left;
          }
          if (top_current < top_peak) {
            top_peak = top_current;
          }
          data_top[index] = top_current;
        }
        else {
          data_top[index] = 0;
        }
        //MID
        if (mid_current < 12) {
          if (mid_left == 0) {
            mid_left = mid_current;
            mid_peak = mid_left;
          }
          if (mid_current < mid_peak) {
            mid_peak = mid_current;
          }
          data_mid[index] = mid_current;
        }
        else {
          data_mid[index] = 0;
        }
        isReading = true;
        index++;

      }
      else {
        if (isReading) {

          for (int x = 0; x < index ; x++) {
            if (data_top[x] != 0) {
              top_right = data_top[x];
            }
            if (data_mid[x] != 0) {
              mid_right = data_mid[x];
            }
          }
          while (data_top[delta_count] == 0 && delta_count < index) {
            delta_left--;
            delta_count++;
          }
          delta_count = 0;

          while (data_mid[delta_count] == 0 && delta_count < index) {
            delta_left++;
            delta_count++;
          }

          for (int x = index; x >= 0; x--) {
            if (data_top[x] == 0) {
              delta_right++;
            }
            if (data_mid[x] == 0) {
              delta_right--;
            }
          }

          float delta_pitch = top_peak - mid_peak;
          delta_yaw = (delta_left + delta_right * (1000.0 / fps));

          Serial.print("former?deltaYaw=");
          Serial.print(delta_yaw);
          Serial.print("&deltaPitch=");
          Serial.println(delta_pitch);

          Serial.print("formerRaw?topPeak=");
          Serial.print(top_peak);
          Serial.print("&midPeak=");
          Serial.print(mid_peak);
          Serial.print("&deltaLeft=");
          Serial.print(delta_left);
          Serial.print("&deltaRight=");
          Serial.println(delta_right);

          //RESET//

          memset(data_top, -1, sizeof(data_top));
          memset(data_mid, -1, sizeof(data_mid));

          top_left = 0;
          top_peak = 0;
          top_right = 0;

          mid_left = 0;
          mid_peak = 0;
          mid_right = 0;

          delta_right = 0;
          delta_left = 0;
          delta_top = 0;

          isReading = false;
          index = 0;
          //                chain_interval = 0;

        }
      }
    }
    //      chain_interval += 1000/fps;
    startTime = millis();
  }
}
