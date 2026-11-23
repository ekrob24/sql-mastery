# Learning roadmap

Run `python3 sqlm.py` anytime to see this roadmap with your progress bars.

## Module 1 — SQL foundations  (8 lessons, 50 exercises)

1. **SELECT, FROM, aliases, and reading a table** — 6 exercises · `lessons/module_01_foundations/lesson_01_select_from_aliases/lesson.md`
2. **Filtering with WHERE, AND, OR, NOT, IN, BETWEEN, LIKE** — 7 exercises · `lessons/module_01_foundations/lesson_02_filtering_where/lesson.md`
3. **Handling NULLs correctly** — 6 exercises · `lessons/module_01_foundations/lesson_03_handling_nulls/lesson.md`
4. **Sorting and limiting results** — 6 exercises · `lessons/module_01_foundations/lesson_04_sorting_limiting/lesson.md`
5. **DISTINCT and removing duplicates** — 6 exercises · `lessons/module_01_foundations/lesson_05_distinct_duplicates/lesson.md`
6. **Aggregations: COUNT, SUM, AVG, MIN, MAX** — 6 exercises · `lessons/module_01_foundations/lesson_06_aggregations/lesson.md`
7. **GROUP BY** — 6 exercises · `lessons/module_01_foundations/lesson_07_group_by/lesson.md`
8. **HAVING versus WHERE** — 7 exercises · `lessons/module_01_foundations/lesson_08_having_vs_where/lesson.md`

## Module 2 — Joins  (11 lessons, 69 exercises)

9. **Keys and relationships** — 6 exercises · `lessons/module_02_joins/lesson_09_keys_and_relationships/lesson.md`
10. **INNER JOIN** — 6 exercises · `lessons/module_02_joins/lesson_10_inner_join/lesson.md`
11. **LEFT JOIN** — 6 exercises · `lessons/module_02_joins/lesson_11_left_join/lesson.md`
12. **RIGHT JOIN** — 6 exercises · `lessons/module_02_joins/lesson_12_right_join/lesson.md`
13. **FULL OUTER JOIN** — 6 exercises · `lessons/module_02_joins/lesson_13_full_outer_join/lesson.md`
14. **Joining three or more tables** — 6 exercises · `lessons/module_02_joins/lesson_14_multi_table_joins/lesson.md`
15. **Self joins** — 6 exercises · `lessons/module_02_joins/lesson_15_self_joins/lesson.md`
16. **Row multiplication and duplicate detection** — 7 exercises · `lessons/module_02_joins/lesson_16_row_multiplication_duplicates/lesson.md`
17. **Anti-joins: LEFT JOIN ... IS NULL and NOT EXISTS** — 7 exercises · `lessons/module_02_joins/lesson_17_anti_joins/lesson.md`
18. **NATURAL JOIN: mechanics and risks** — 6 exercises · `lessons/module_02_joins/lesson_18_natural_join/lesson.md`
19. **LATERAL JOIN: correlated row-level subqueries** — 7 exercises · `lessons/module_02_joins/lesson_19_lateral_join/lesson.md`

## Module 3 — Query composition  (9 lessons, 59 exercises)

> 🔒 **Gate:** pass `python3 sqlm.py checkpoint` (join mastery) to unlock Module 3 onward.

20. **CASE WHEN** — 7 exercises · `lessons/module_03_query_composition/lesson_20_case_when/lesson.md`
21. **Subqueries in WHERE** — 7 exercises · `lessons/module_03_query_composition/lesson_21_subqueries_in_where/lesson.md`
22. **Subqueries in FROM** — 6 exercises · `lessons/module_03_query_composition/lesson_22_subqueries_in_from/lesson.md`
23. **Correlated subqueries** — 6 exercises · `lessons/module_03_query_composition/lesson_23_correlated_subqueries/lesson.md`
24. **EXISTS and NOT EXISTS** — 7 exercises · `lessons/module_03_query_composition/lesson_24_exists_not_exists/lesson.md`
25. **UNION, UNION ALL, INTERSECT, EXCEPT** — 7 exercises · `lessons/module_03_query_composition/lesson_25_set_operations/lesson.md`
26. **CTEs** — 6 exercises · `lessons/module_03_query_composition/lesson_26_ctes/lesson.md`
27. **Multi-CTE analytical queries** — 6 exercises · `lessons/module_03_query_composition/lesson_27_multi_cte_pipelines/lesson.md`
28. **Recursive CTEs** — 7 exercises · `lessons/module_03_query_composition/lesson_28_recursive_ctes/lesson.md`

## Module 4 — Analytical SQL  (12 lessons, 79 exercises)

29. **Date functions and time-based filtering** — 6 exercises · `lessons/module_04_analytical_sql/lesson_29_date_functions/lesson.md`
30. **Daily, weekly, monthly, and yearly aggregation** — 7 exercises · `lessons/module_04_analytical_sql/lesson_30_period_aggregation/lesson.md`
31. **Year-over-year and month-over-month analysis** — 7 exercises · `lessons/module_04_analytical_sql/lesson_31_yoy_mom_analysis/lesson.md`
32. **Running totals** — 7 exercises · `lessons/module_04_analytical_sql/lesson_32_running_totals/lesson.md`
33. **Moving averages** — 6 exercises · `lessons/module_04_analytical_sql/lesson_33_moving_averages/lesson.md`
34. **ROW_NUMBER, RANK, and DENSE_RANK** — 7 exercises · `lessons/module_04_analytical_sql/lesson_34_ranking_functions/lesson.md`
35. **LAG and LEAD** — 6 exercises · `lessons/module_04_analytical_sql/lesson_35_lag_and_lead/lesson.md`
36. **PARTITION BY and window frames** — 7 exercises · `lessons/module_04_analytical_sql/lesson_36_partition_by_and_window_frames/lesson.md`
37. **Pivoting and unpivoting** — 6 exercises · `lessons/module_04_analytical_sql/lesson_37_pivoting_and_unpivoting/lesson.md`
38. **Cohort retention analysis** — 7 exercises · `lessons/module_04_analytical_sql/lesson_38_cohort_retention_analysis/lesson.md`
39. **Funnel analysis** — 7 exercises · `lessons/module_04_analytical_sql/lesson_39_funnel_analysis/lesson.md`
40. **Revenue, margin, and product-performance analysis** — 6 exercises · `lessons/module_04_analytical_sql/lesson_40_revenue_margin_product_performance/lesson.md`

## Module 5 — Snowflake readiness  (10 lessons, 67 exercises)

41. **Snowflake SQL differences and syntax awareness** — 6 exercises · `lessons/module_05_snowflake_readiness/lesson_41_snowflake_sql_differences/lesson.md`
42. **Querying semi-structured JSON-like data** — 6 exercises · `lessons/module_05_snowflake_readiness/lesson_42_querying_json_data/lesson.md`
43. **VARIANT, OBJECT, ARRAY concepts** — 6 exercises · `lessons/module_05_snowflake_readiness/lesson_43_variant_object_array/lesson.md`
44. **FLATTEN and LATERAL for nested data** — 7 exercises · `lessons/module_05_snowflake_readiness/lesson_44_flatten_and_lateral/lesson.md`
45. **Query readability and CTE pipelines** — 6 exercises · `lessons/module_05_snowflake_readiness/lesson_45_cte_pipelines/lesson.md`
46. **Query-performance concepts** — 6 exercises · `lessons/module_05_snowflake_readiness/lesson_46_query_performance_concepts/lesson.md`
47. **Identifying redundant joins** — 6 exercises · `lessons/module_05_snowflake_readiness/lesson_47_redundant_joins/lesson.md`
48. **Debugging incorrect row counts** — 7 exercises · `lessons/module_05_snowflake_readiness/lesson_48_debugging_row_counts/lesson.md`
49. **Data-quality validation queries** — 7 exercises · `lessons/module_05_snowflake_readiness/lesson_49_data_quality_validation/lesson.md`
50. **Capstone analytics project: E-commerce Performance Review** — 10 exercises · `lessons/module_05_snowflake_readiness/lesson_50_capstone_ecommerce_performance_review/lesson.md`

**Total:** 50 lessons, 324 exercises.
