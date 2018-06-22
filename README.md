# gs1-cloud

Program to CHECK the validity of GTINS/EAN codes against the GS1 Cloud (BETA) CHECK API

Install the program on your local machine. It's written in Python 3.

Put your credentials (email and api-key) in the file credentials.py

Add your set of GTINS in the file gtins.txt. The program has been tested with up to 500.000 GTINS in one file.
The GTINS have to be 14 digits long, including leading zero's.

Run the program. It will test about 35 GTINS per second.

Find the output in .\output\Tested_gtins_yyyymmdd_hhmmss.csv
Also a log file is created as .\output\Tested_gtins_yyyymmdd_hhmmss.log

You can contact your the GS1 Member Organisation in your country for possibilities to participate in the beta-program.
For more information www.gs1.org
