# Decision Log
1. Python 3.10+ selected; standard library only.
2. Master/sample data and distance table embedded in Python as requested.
3. `Decimal` used for all monetary and percentage calculations.
4. Price modifiers are additive percentage points on base freight, rounded once to whole rupees.
5. Surge thresholds use strict greater-than comparisons; 0.5 lower threshold is strict less-than.
6. Truck size order is LCV, 17FT, 22FT, 32FT_MXL, trailer; at most one category larger.
7. Top three trucks are queued sequentially; acceptance, decline and timeout are explicit commands/events.
8. Toll cap is a Python lane dictionary; actual toll is limited to 110% of configured cap.
9. TDS is assessed if the trip payout exceeds ₹30,000 or cumulative annual payout after the trip exceeds ₹1,00,000.
10. Hidden evaluator parity cannot be asserted without the organizer's sample inputs and expected outputs.
