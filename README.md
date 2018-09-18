# GS1 Cloud GTIN CHECK (beta) and GTIN VIEW (experimental)

Programs to CHECK the validity of GTINS/EAN codes against the GS1 Cloud (BETA) CHECK API and VIEW the active GTINS from the VIEW API (experimental)

The GS1 Cloud will be the largest source of trusted product information in the world, making it possible for businesses to meet the expectations of today’s digital world.
For more information <a href="https://www.gs1.org/services/gs1-cloud" target="_blank">GS1.org</a>.

**Install and usage notes**

1. Install Python 3 <a href="https://www.python.org/" target="_blank">(www.python.org)</a> on your computer.
2. Download the zip file with the program files on your local machine. Unpack and store it in a local map.
3. Put your credentials (email and api-key) in the file credentials.py.
   The API key can be found in the <a href="https://cloud.gs1.org/gs1-portal/" target="_blank">GS1 Cloud user interface</a>
   under 'Account'.
4. If Python indicates that there are any missing packages use PIP to add them (e.g. ..>pip install requests).

Please note:<br>
As the program might run for several hours in case of large input files it can be preferable to install it on a server in stead of a personal laptop.

**CHECK GS1_Cloud_CHECK_GTINS.py**
1. Perform a test run with the attached file sample_gtins.txt. This will generate all of the current messages.
2. Add your set of GTINS in the file "your filename".txt in the directory "input"<br>
   The GTINS have to be 14 digits long, including leading zero's.
3. Refer to the correct filename in the file config.py.   
4. Adjust the basic settings (as output language etc.) in the file config.py
5. Run the program in the shell program of your OS (..>python GS1_Cloud_CHECK_GTINS.py) or a Python IDE.<br>
   The program has been tested with up to 1.500.000 GTINS in one file. The speed depends on the settings in the config file (poolsize and batchsize).
6. Find the output in the directory "output" as "your filename"_check_yyyymmdd_hhmmss.csv.<br>
   All invalid gtins are also listed "your filename"_check_invalid_yyyymmdd_hhmmss.csv. This is usefull in case of large datasets.
   Also a log file is created as "your filename"_check_yyyymmdd_hhmmss.log<br>
7. Two files are added to the input directory:   
   - All the unique GTINS from the input file are copied into to "your filename"_unique.txt<br>
   - All active GTINS are listed in the file "your filename"_active.txt. This file is used as input for GS1_Cloud_VIEW_GTINS.py
8. View and analyze your results in a spreadsheet or database.

**VIEW GS1_Cloud_VIEW_GTINS.py**<br>
Please note:<br>
The VIEW API is experimental and at the moment only available for GS1 member organisations.
At this moment you can only view items uploaded under your account. Therefor many active gtins (from other sources)
give a 404 (not found) as result. These are listed in the log file.  

1. Run the Check program first in order to identify all the active GTINS.<br>
2  Run the program in the shell program of your OS (..>python GS1_Cloud_VIEW_GTINS.py) or a Python IDE.<br>
3. Find the output in the directory output as "your filename"_view_yyyymmdd_hhmmss.csv.<br>
   Also a log file in the directory output is created as "your filename"_view_yyyymmdd_hhmmss.log<br>
4. View and analyze your results in a spreadsheet or database.
