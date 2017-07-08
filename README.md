# dynamic_testing
Dynamic UI testing based on test cases using Selenium and Python's unittest

A dynamic testing framework that I built for my company using Selenium and Python. 

This repository is a use case of the testing framework; testing the flow of a complex Kitting process. Kitting is a complex warehousing process where when one receive a set of assembled parts, one must track the parts inside (and take note of their conditions) and make sure that the kit is complete. For example, when we receive an Airplane engine, we must confirm that the parts inside are present to make sure that it has the essential parts needed for it to work, even if it means we have to assemble it back later on. By confirming which parts are missing from the kit, the sales team can then also renegotiate with the seller regarding the price of the kit (i.e. if it is missing a valuable part, the kit should be valued lower than it actually is). More importantly, by knowing which parts are missing, broken, or wear, the assembly crew can then add replace these faulty parts and assemble the kit back for the company to sell it at a higher value. You can imagine how complex and long the process is, that is why I created a dynamic testing framework/platform to help me test the flow of the whole project against multiple test cases.

I was the one in charge of the Kitting project, but I do not think that I can upload it to my Github since it would reveal my company's database schema and other configurations for hackers to exploit. I can however, upload this test framework since it does not consist any company secrets.

This test example is testing 3 web applications (Kit Receiving, Kit Tree, and Kit List Edit) against 7 test cases (in JSON format for its readability, extensibility, and universal formatting). In the framework, I outlined three major steps for testing: EXISTING, INSERTING, and MATCHING. 
- EXISTING: inputs any data that should be prepopulated either in database or in the webbrowser
- INSERTING: the "action" bit of the testing, where data will be manipulated
- MATCHING: the expected results of the whole process; it can be in the form of checking the database for our expected result or to check the website for an expected response

The `kit_master_test.py` is the main program that will call the other test classes and set their parameters to run on different test cases.
