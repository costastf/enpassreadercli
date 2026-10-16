.. :changelog:

History
-------

0.0.1 (27-03-2021)
---------------------

* First code creation


0.1.0 (27-03-2021)
------------------

* Initial functionality.


0.1.1 (27-03-2021)
------------------

* Reverted to default styling for search function.


0.2.0 (27-03-2021)
------------------

* Added fuzzy searching capabilities.


0.2.1 (07-07-2021)
------------------

* Added pipeline and bumped dependencies.


0.3.0 (02-03-2023)
------------------

* Implement totp retrieval.


0.3.1 (02-03-2023)
------------------

* Calculate actual totp from provided seed and return that.


0.4.0 (10-08-2023)
------------------

* Implement support for pbkdf2-rounds setting as an argument.


0.4.1 (10-08-2023)
------------------

* Fix requirements on the pipeline for upload.


0.4.2 (10-08-2023)
------------------

* Improve error message where pbkdf2 round value could be wrong.


0.5.0 (16-10-2026)
------------------

* - Read any field of an entry by label with -F/--field, prompting for it in interactive search.
* - Do not crash on entries without a totp seed. Require Python 3.11 and enpassreaderlib 0.3.0.


0.5.1 (16-10-2026)
------------------

* Bump dependencies.


0.5.2 (16-10-2026)
------------------

* Require enpassreaderlib 0.4.1 which verifies the authentication tag of encrypted values and opens the database read only.
* Report values that fail authentication instead of crashing, skipping them when enumerating and exiting with an error.
* Report invalid key files and missing database paths with their own error messages.
* Close the database connection when done.
