# Citations

## Reference List

1. Abiteboul S, Duschka OM (1998) Complexity of answering queries using materialized views. In: PODS, pp 254–263
2. Bohannon P, Freire J, Haritsa JR, Ramanath M, Roy P, Sim­éon J (2002) LegoDB: Customizing relational storage for XML documents. In: VLDB, pp 1091–1094
3. Bertino E, Haas LM, Lindsay BG (1983) View management in distributed data base systems. In: VLDB, pp 376–378
4. Banerjee J, Kim W, Kim H, Korth HF (1987) Semantics and implementation of schema evolution in object-oriented databases. In: SIGMOD, pp 311–322
5. Bernstein P, Rahm E (2003) Data warehouse scenarios for model management. Inf Sys, pp 1–15
6. Claypool KT, Jin J, Rundensteiner EA (1998) SERF: Schema evolution through an extensible re-usable and flexible FRAMEWORK. In: CIKM, pp 314–321
7. Ceri S, Widom J (1991) Deriving production rules for incremental view maintenance. In: VLDB, pp 577–589
8. Florescu D, Kossmann D (1999) Storing and querying XML data using an RDBMS. IEEE Data Eng Bull 22(3):27–34
9. Fagin R, Kolaitis PG, Miller RJ, Popa L (2002) Data exchange: semantics and query answering. In: ICDT, pp 207–224
10. Fagin R, Kolaitis P, Popa L, Tan W (2004) Composing schema mappings: second-order dependencies to the rescue. In: PODS
11. Gyssens M, Lakshmanan L, Subramanian IN (1995) Tables as a paradigm for querying and restructuring. In: PODS, pp 93–103
12. Friedman M, Levy A, Millstein T (1999) Navigational plans for data integration. In: AAAI, pp 67–73
13. Gupta A, Mumick L, Ross K (1995) Adapting materialized views after redefinition. In: SIGMOD, pp 211–222
14. Halevy A, Ives Z, Suciu D, Tatarinov I (2003) Schema mediation in peer data management systems. In: ICDE, pp 505–517
15. Kawecka M, Mannila H, Räihä K-J, Sirrota H (1992) Discovering functional and inclusion dependencies in relational databases. Int J Intell Sys 7(7):591–607
16. Kotidis Y, Roussopoulos N (2001) DynaMat: a dynamic view management system for data warehouses. In: SIGMOD, pp 371–382
17. Kotidis Y, Roussopoulos N (2001) A case for dynamic view management. ACM Trans Database Sys 26(4):388–423
18. Lerner BS (2000) Data migration: a theoretical perspective. In: PODS, pp 233–246
19. Lerner BS (2000) A model for compound type changes encountered in schema evolution. ACM Trans Database Sys 25(1):83–127
20. Lee AJ, Nica A, Rundensteiner EA (2002) The EVE approach: view synchronization in dynamic distributed environments. Trans Knowl Data Eng 14(5):931–954
21. Levy AY, Rajaraman A, Ordille JJ (1996) Querying heterogeneous information sources using source descriptions. In: VLDB, pp 251–262
22. Madhavan J, Bernstein P, Rahm E (2001) Generic schema matching with Cupid. In: VLDB, pp 49–58
23. Mohania MK, Dong G (1996) Algorithms for adapting materialised views in data warehouses. In: CODAS, pp 309–316
24. Madhavan J, Halevy AY (2003) Composing mappings among data sources. In: VLDB
25. Miller RJ, Haas LM, Hernandez M (2003) Schema mapping as query discovery. In: VLDB, pp 77–88
26. Maier D, Mendelzon AO, Sagiv Y (1979) Testing implications of data dependencies. ACM Trans Database Syst 4(4):455–469
27. McBrien P, Poulovassilis A (2002) Schema evolution in heterogeneous database architectures, a schema transformation approach. In: CAiSE, pp 484–499
28. Mumick IS, Quass D, Mumick BS (1997) Maintenance of data cubes and summary tables in a warehouse. In: SIGMOD, pp 100–111
29. Melnik S, Rahm E, Bernstein P (2003) Rondo: a programming platform for generic model management. In: SIGMOD, pp 193–204
30. Popa L, Tannen V (1999) An equational chase for path-conjunctive queries, constraints, and views. In: ICDT, pp 39–57
31. Popa L, Velegrakis Y, Miller RJ, Hernandez MA, Fagin R (2002) Translating Web data. In: VLDB, pp 598–609
32. Rahm E, Bernstein PA (2001) A survey of approaches to automatic schema matching. VLDB J 10(4):334–350
33. Spaccapietra S, Parent C (1994) View integration: a step forward in solving structural conflicts. Trans Knowl Data Eng 6(2):258–274
34. Shamir R, Tsur D (1999) Faster subtree isomorphism. J Algorithms 33(2):267–280
35. Velegrakis Y (2004) Managing schema mappings in highly heterogeneous environments. PhD thesis, University of Toronto (in preparation)
36. Velegrakis Y, Miller RJ, Popa L (2003) Mapping adaptation under evolving schemas. In: VLDB, pp 584–595
37. Vassalos V, Papakonstantinou Y (1997) Describing and using query capabilities of heterogeneous sources. In: VLDB, pp 256–265
38. W3C (2001) XML Schema Part 0: Primer. http://www.w3.org/TR/xmlschema-0/, W3C Recommendation
39. Widom J (1995) Research problems in data warehousing. In: CIKM, pp 25–30

## Key Citations for Follow-up

- **[26] Maier, Mendelzon, Sagiv (1979) "Testing implications of data dependencies"** — Provides the chase algorithm and its `O(k^L · 2^k · log k · n)` complexity bound that underpins ToMAS's logical-association computation. Directly relevant if propstore implements a chase-style migration evaluator.
- **[29] Melnik, Rahm, Bernstein (2003) "Rondo: a programming platform for generic model management"** — The compose-based alternative to ToMAS. Velegrakis identifies trade-offs (Rondo handles old/new schema diff but ignores user-mapping batch). Worth reading to understand both poles of mapping-adaptation design.
- **[31] Popa, Velegrakis, Miller, Hernandez, Fagin (2002) "Translating Web data"** — Defines the Clio mapping language ToMAS extends. Required prerequisite for the formal substrate.
- **[25] Miller, Haas, Hernandez (2003) "Schema mapping as query discovery"** — Clio mapping discovery. Together with [31], the from-scratch baseline ToMAS competes against.
- **[36] Velegrakis, Miller, Popa (2003) "Mapping adaptation under evolving schemas"** — VLDB conference version. May contain shorter/different exposition and worth scanning for changes between conference and journal.
- **[24] Madhavan, Halevy (2003) "Composing mappings among data sources"** — The compose operator that powers Rondo. Important to understand how propstore could combine ToMAS-style operator decomposition with composition over disjoint changes.
