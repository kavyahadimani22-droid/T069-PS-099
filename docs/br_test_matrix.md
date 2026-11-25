# Business Rule to Test Traceability Matrix (BR-01 to BR-30)

| Rule ID | Business Rule Summary | Implementation Module & Function | Automated Test(s) | Sample Pack Check |
|---|---|---|---|---|
| **BR-01** | Base price = `max(km, 150) * requested_rate` | `pricing_service.py::price_load` | `test_min_chargeable_distance_149_to_150` | `BR-01_min_150_km` |
| **BR-02** | Unknown city pair raises error | `exceptions.py::lane_km` | `test_unknown_lane_raises_rule_error` | &mdash; |
| **BR-03** | Demand/supply ratio within 200 km of origin | `pricing_service.py::price_load` | `test_exact_15_ratio_has_no_surge` | `price_breakdowns.csv` |
| **BR-04** | Surge bands (`>4: +30%`, `>2.5: +20%`, `>1.5: +10%`, `<0.5: -10%`) | `pricing_service.py::calculate_surge_modifier` | `test_surge_over_4_adds_30_pct`, `test_low_demand_below_half_deducts_10_pct` | `price_breakdowns.csv` |
| **BR-05** | `>=3` return loads within 300 km &rarr; `-8%` | `pricing_service.py::price_load` | `test_return_load_discount_with_three_qualifying_loads` | `BR-05_return_load_discount` |
| **BR-06** | Backhaul-poor destination &rarr; `+12%` | `pricing_service.py::price_load` | `test_backhaul_poor_and_hazardous_additive` | `BR-06_07_poor_and_hazmat` |
| **BR-07** | Hazardous `+15%` + `haz_certified` required | `pricing_service.py`, `matching_service.py` | `test_backhaul_poor_and_hazardous_additive`, `test_haz_cert_required` | `BR-06_07_poor_and_hazmat` |
| **BR-08** | Perishable `+10%` + pickup window `<=6h` | `pricing_service.py::validate_load` | `test_perishable_over_6h_rejected` | `BR-08_perishable_surcharge` |
| **BR-09** | Oversize length `> truck.length_ft` ineligible | `matching_service.py::evaluate_truck_eligibility` | `test_oversize_length_rejected` | `LD-006` |
| **BR-10** | Capacity covers weight; exact or +1 truck size | `matching_service.py::evaluate_truck_eligibility` | `test_one_size_larger_truck_allowed` | `rejections.csv` |
| **BR-11** | Available by `pickup_end` and `<=150 km` from origin | `matching_service.py::evaluate_truck_eligibility` | `test_truck_exact_150_km_is_eligible`, `test_truck_over_150_km_rejected` | `rejections.csv` |
| **BR-12** | Driver hours cover `km/40 + 2h` buffer (`second_driver` waives) | `matching_service.py::evaluate_truck_eligibility` | `test_hos_exact_buffer_allowed`, `test_second_driver_waives_hos_rejection` | `BR-12_26_hos_rejection` |
| **BR-13** | Rank `(km asc, rating desc, truck_id asc)`; top 3 offered | `matching_service.py::eligible_trucks`, `freight_engine.py` | `test_rating_below_3_excluded_and_ranking_tie_break` | `trips.csv` |
| **BR-14** | Offer expires after 30 min &rarr; next ranked truck | `freight_engine.py::advance`, `respond_offer` | `test_offer_timeout_moves_to_next_ranked_truck` | &mdash; |
| **BR-15** | Counter `>15%` rejected; `<=15%` evaluated | `bidding_service.py::counter_status` | `test_counter_thresholds` | `BR-16_counter_accepted` |
| **BR-16** | Counter `<=5%` auto-accepted; `5-15%` 60-min shipper window | `bidding_service.py`, `freight_engine.py` | `test_counter_shipper_window_accept` | `BR-16_counter_accepted` |
| **BR-17** | 6 free detention hours; round up separately | `trip_lifecycle_service.py::detention` | `test_detention_6h1m_and_48h_cap` | `settlements.csv` |
| **BR-18** | Detention ₹300/₹500/₹800 per hr, max 48 hrs | `trip_lifecycle_service.py::detention` | `test_detention_6h1m_and_48h_cap` | `BR-19_abort_compensation` |
| **BR-19** | Abort after 48h &rarr; capped detention + 50% base | `freight_engine.py::event` (`ABORT`) | `test_no_show_and_abort_workflows` | `BR-19_abort_compensation` |
| **BR-20** | Shipper cancel: `<=1h` free, `<=6h` ₹1,000, `>6h` 10% base | `trip_lifecycle_service.py::cancellation_fee` | `test_shipper_cancellation_tiers` | `BR-20_shipper_cancel_1000` |
| **BR-21** | Carrier cancel / no-show: ₹2,000 + rating `-0.2` | `freight_engine.py::event` | `test_no_show_and_abort_workflows` | `BR-21_carrier_cancel_2000` |
| **BR-22** | Carrier receipt: freight + detention + toll (`cap * 1.10`) | `settlement_service.py::settle` | `test_toll_cap_and_rcm_settlement` | `BR-22_toll_cap_110pct` |
| **BR-23** | Platform fee = 6% of base freight | `settlement_service.py::settle` | `test_toll_cap_and_rcm_settlement` | `settlements.csv` |
| **BR-24** | Shipper invoice adds 5% GST on freight + RCM flag | `settlement_service.py::settle` | `test_toll_cap_and_rcm_settlement` | `BR-24_gst_rcm_flags` |
| **BR-25** | 1% TDS if payout `>30k` or annual cumulative `>1L` | `settlement_service.py::settle` | `test_cumulative_tds_crossing_100k`, `test_tds_not_charged_at_exact_30000_before_tds` | `BR-25_cumulative_and_trip_tds` |
| **BR-26** | 14h daily HOS limit (`trip_km/40 + 1`) | `matching_service.py::evaluate_truck_eligibility` | `test_second_driver_waives_hos_rejection` | `BR-12_26_hos_rejection` |
| **BR-27** | Rating `4.0` start; `+0.05` / `-0.1` / `-0.2`; clamp `1.0-5.0` | `trip_lifecycle_service.py::update_rating` | `test_rating_bounds` | `BR-27_rating_update` |
| **BR-28** | Rating `<3.0` excluded from ranking | `matching_service.py::evaluate_truck_eligibility` | `test_rating_below_3_excluded_and_ranking_tie_break` | `BR-28_low_rating_excluded` |
| **BR-29** | Optional multi-drop extra stop fee (`extra_stops`) | `pricing_service.py::price_load` | `test_optional_multidrop_and_fuel_index` | Simulator UI |
| **BR-30** | Optional monthly fuel-price index (`fuel_index_pct`) | `pricing_service.py::price_load` | `test_optional_multidrop_and_fuel_index` | Simulator UI |
