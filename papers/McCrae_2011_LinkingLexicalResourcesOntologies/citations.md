# Citations

## Reference List

1. Bizer, C., Heath, T., Berners-Lee, T.: Linked data-the story so far. International Journal on Semantic Web and Information Systems 5(3), 1-22 (2009)
2. Bontcheva, K.: Generating tailored textual summaries from ontologies. In: Gómez-Pérez, A., Euzenat, J. (eds.) ESWC 2005. LNCS, vol. 3532, pp. 531-545. Springer, Heidelberg (2005)
3. Brickley, D., Miller, L.: FOAF Vocabulary Specification 0.98 (2010) (accessed December 3, 2010)
4. Buitelaar, P.: Ontology-based Semantic Lexicons: Mapping between Terms and Object Descriptions. In: Ontology and the Lexicon, pp. 212-223. Cambridge University Press, Cambridge (2010)
5. Chiarcos, C.: Grounding an Ontology of Linguistic Annotations in the Data Category Registry. In: Proceedings of the 2010 International Conference on Language Resource and Evaluation, LREC (2010)
6. Cimiano, P., Buitelaar, P., McCrae, J., Sintek, M.: LexInfo: A Declarative Model for the Lexicon-Ontology Interface. Web Semantics: Science, Services and Agents on the World Wide Web 9(1), 29-51 (2011)
7. Collier, N., Doan, S., Kawazoe, A., Goodwin, R., Conway, M., Tateno, Y., Ngo, Q., Dien, D., Kawtrakul, A., Takeuchi, K., Shigematsu, M., Taniguchi, K.: BioCaster: detecting public health rumors with a Web-based text mining system. Oxford Bioinformatics 24(24), 2940-2941 (2008)
8. Farrar, S., Langendoen, D.: Markup and the GOLD Ontology. In: Proceedings of Workshop on Digitizing and Annotating Text and Field Recordings (2003)
9. Fellbaum, C.: WordNet: An electronic lexical database. MIT Press, Cambridge (1998)
10. Francopoulo, G., George, M., Calzolari, N., Monachini, M., Bel, N., Pet, M., Soria, C.: Lexical markup framework (LMF). In: Proceedings of the Fifth International Conference on Language Resource and Evaluation (LREC 2006) (2006)
11. Gangemi, A., Guarino, N., Masolo, C., Oltramari, A.: Sweetening wordnet with DOLCE. AI Magazine 24(3), 13 (2003)
12. Gangemi, A., Navigli, R., Velardi, P.: The ontoWordNet project: Extension and axiomatization of conceptual relations in wordNet. In: Chung, S., Schmidt, D.C. (eds.) CoopIS 2003, DOA 2003, and ODBASE 2003. LNCS, vol. 2888, pp. 820-838. Springer, Heidelberg (2003)
13. Kemps-Snijders, M., Windhouwer, M., Wittenburg, P., Wright, S.: ISOcat: Corralling data categories in the wild. In: Proceedings of the 2008 International Conference on Language Resource and Evaluation, LREC (2008)
14. Kilgarriff, A.: I Don't Believe in Word Senses. Computers and the Humanities 31(2), 91-113 (1997)
15. Klein, D., Manning, C.: Accurate unlexicalized parsing. In: Proceedings of the 41st Annual Meeting on Association for Computational Linguistics, pp. 423-430 (2003)
16. Korhonen, A., Krymolowski, Y., Briscoe, T.: A large subcategorization lexicon for natural language processing applications. In: Proceedings of the Fifth International Conference on Language Resources and Evaluation, LREC 2006 (2006)
17. Lopez, V., Pasin, M., Motta, E.: AquaLog: An ontology-portable question answering system for the semantic web. In: Gómez-Pérez, A., Euzenat, J. (eds.) ESWC 2005. LNCS, vol. 3532, pp. 546-562. Springer, Heidelberg (2005)
18. Miles, A., Bechhofer, S.: SKOS Simple Knowledge Organization System Reference (2009) (accessed October 19, 2010)
19. Romary, L.: Standardization of the formal representation of lexical information for NLP. In: Dictionaries: An International Encyclopedia of Lexicography. Mouton de Gruyter, Berlin (2010)
20. Sagot, B.: The Lefff, a freely available and large coverage morphological and syntactic lexicon for French. In: Proceedings of the 2010 International Conference on Language Resource and Evaluation (LREC) (2010)
21. Smith, B., Ashburner, M., Rosse, C., Bard, J., Bug, W., Ceusters, W., Goldberg, L., Eilbeck, K., Ireland, A., Mungall, C., et al.: The OBO Foundry: coordinated evolution of ontologies to support biomedical data integration. Nature Biotechnology 25(11), 1251-1255 (2007)
22. Spackman, K., Campbell, K., Côté, R.: SNOMED RT: a reference terminology for health care. In: Proceedings of the AMIA Annual Fall Symposium, pp. 640-644 (1997)
23. Toutanova, K., Klein, D., Manning, C., Singer, Y.: Feature-rich part-of-speech tagging with a cyclic dependency network. In: Proceedings of the 2003 Conference of the North American Chapter of the Association for Computational Linguistics on Human Language Technology, pp. 173-180 (2003)
24. Van Assem, M., Gangemi, A., Schreiber, G.: Conversion of WordNet to a standard RDF/OWL representation. In: Proceedings of the Fifth International Conference on Language Resources and Evaluation, LREC 2006 (2006)

## Key Citations for Follow-up

- **[6] Cimiano, Buitelaar, McCrae, Sintek — LexInfo (2011).** Direct predecessor model that lemon-LexInfo extends. Needed to understand the pre-lemon separation between linguistic and semantic-syntactic layers, and to see which LMF assumptions the 2011 paper inherits vs replaces.
- **[14] Kilgarriff — I Don't Believe in Word Senses (1997).** Grounding for lemon's most non-commitment-aligned design choice: LexicalSense is not assumed finite or disjoint. Important for propstore because the same argument sustains the project's storage-level non-commitment principle.
- **[11] Gangemi, Guarino, Masolo, Oltramari — Sweetening WordNet with DOLCE (2003).** Cited to back the claim that WordNet's conceptual model is "unsound from an ontological perspective". Relevant for deciding whether propstore should ingest WordNet directly or via a DOLCE-bridged ontology.
- **[13] Kemps-Snijders et al. — ISOcat (2008).** Source of the data-category URIs (e.g., `isocat:DC-1298`) imported wholesale into lemon-LexInfo. propstore will need to decide whether to use ISOcat or a modern successor registry.
- **[10] Francopoulo et al. — LMF (2006).** Parent standard. lemon explicitly is *not* technically an instance of LMF but many aspects correspond; the lemon↔LMF converter lives at `http://www.lexinfo.net/lemon2lmf`.
