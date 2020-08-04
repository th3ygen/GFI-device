#include <MovingAverageFilter.h>
#include <MegunoLink.h>

#include <Filter.h>

MovingAverageFilter chainAverageFilter(20);
MovingAverageFilter chain1AverageFilter(12.5);
ExponentialFilter<float> chain_filter(10, 4);
ExponentialFilter<float> chain1_filter(10, 3);


unsigned long startTime;
int fps = 800;
float scanZone = 20;
float threshold = 5.5;
float reset_threshold = 0;
int count = 0;
int reset = 0;

float chainInterval = 0;
bool isReading = false;


void setup() {
  startTime - millis();
  Serial.begin(57600);

}

void loop() {
  unsigned long curTime = millis();
  float volts, chain, chain1, chain_1filter,chain_2filter, chain1_1filter, chain1_2filter;

  if (curTime > startTime + (1000 / fps)) {

    volts = analogRead(A2) * 0.0048828125;
    chain = 13 * pow(volts, -1);

    volts = analogRead(A4) * 0.0048828125;
    chain1 = 13 * pow(volts, -1);

    chain_1filter = chainAverageFilter.process(chain);
    chain1_1filter = chain1AverageFilter.process(chain1);

    chain_filter.Filter(chain_1filter);
    chain1_filter.Filter(chain1_1filter);

    chain_2filter = chain_filter.Current();
    chain1_2filter = chain1_filter.Current();

   // Serial.print(chain_2filter);
   // Serial.print(",");
    Serial.println(chain1_2filter);
    /*
       DEFAULT: 11.9-12.5 CM
       CHAIN: 7.9-8.5 CM
       RESET: 3.9-4.5 CM
    */

    //       if(chain_now < scanZone){
    //         Serial.print(chain_now);
    //         Serial.print(",");
    //         Serial.println(15);
    ////         Serial.print(4);
    ////         Serial.print(',');
    //
    ////         if (chain_now > threshold) {
    //////          Serial.print(2);
    ////           Serial.println(chain_now);
    ////         }
    //
    ////          chainInterval = 0;
    //       }
    //      chainInterval += 1000/fps;
    startTime = millis();
  }
}
