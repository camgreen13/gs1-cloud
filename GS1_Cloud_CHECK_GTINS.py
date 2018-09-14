#
# Program to CHECK the validity of GTINS against the GS1 Cloud (BETA) CHECK API
#
# Author: Sjoerd Schaper (sjoerd.schaper@gs1.nl)
# Source code available at: https://github.com/sjoerdsch/gs1-cloud
#
# Put your credentials (email and api-key) in the file credentials.py
# Basic settings are in the file config.py

import datetime
import json
import time
import requests
import base64
import os
import credentials
import config
import messages
import shutil
from io import open
from queue import Queue
from threading import Thread
from pathlib import Path
from statistics import mean, median


class Worker(Thread):
    """ Thread executing tasks from a given tasks queue """

    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                # An exception happened in this thread
                print(e)
            finally:
                # Mark this task as done, whether an exception happened or not
                self.tasks.task_done()


class ThreadPool:
    """ Pool of threads consuming tasks from a queue """

    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """ Add a task to the queue """
        self.tasks.put((func, args, kargs))

    def map(self, func, args_list):
        """ Add a list of tasks to the queue """
        for args in args_list:
            self.add_task(func, args)

    def wait_completion(self):
        """ Wait for completion of all the tasks in the queue """
        self.tasks.join()


if __name__ == "__main__":

    # Function to be executed in a thread
    def check(GTIN_in):
        global checked, responses_batch, statistics, response_times

        starttime_req = time.time()

        # URL for the production environment of GS1 Cloud
        url = "https://cloud.gs1.org/api/v1/products/%s/check" % GTIN_in

        # URL for the test environment of GS1 Cloud
        # If you want to use the test environment you have to change the API key the credentials file too
        # url = "https://cloud.stg.gs1.org/api/v1/products/%s/check" % GTIN_in

        response = requests.request("GET", url, headers=headers)
        api_status_code = response.status_code
        # print(json.dumps(response.text))

        if api_status_code in (200, 400):
            check_response = json.loads(response.text)

            company = ""
            company_lang = ""
            gcp_company = ""

            if 'exception' in check_response:
                gtin = GTIN_in
                messageId = check_response["messageId"]
                status = 0
            else:
                gtin = check_response["gtin"]
                messageId = check_response["reason"][0]['messageId']
                status = check_response["status"]
                if 'companyName' in check_response:
                    company = check_response["companyName"][0]["value"]
                    company_lang = check_response["companyName"][0]["language"]
                    if company_lang == "":
                        company_lang = "xx"
                if 'gcpCompanyName' in check_response:
                    gcp_company = check_response["gcpCompanyName"]

            if messageId in messages.languages[lang]:
                message_out = messages.languages[lang][messageId]
            else:
                message_out = "Unknown messageId"
                print("Unknown messageId: %s" % messageId)
                log.write("Unknown messageId: %s" % messageId)

            if config.output_to_screen:
                print(api_status_code, status, gtin, messageId, message_out, gcp_company, company)

            output.write('%s|%s|%s|%s|%s|%s|%s \n' % (gtin, status, messageId, message_out, gcp_company, company, company_lang))

            # Write invalid GTINS in extra output file (usefull in case of large datasets)
            if messageId not in ("S002", "S003", "S005"):
                output_inval.write('%s|%s|%s|%s|%s|%s|%s \n' % (gtin, status, messageId, message_out, gcp_company, company, company_lang))

            checked = checked + 1
            responses_batch = responses_batch + 1
            statistics[messageId] = statistics[messageId] + 1

            if messageId in ("S003", "S005"):
                active_gtins.write('%s\n' % (gtin))
        else:
            if api_status_code == 401:
                print('Full authentication is required to access this resource')
            elif api_status_code == 500:
                log.write('%s %s GTIN not accepted in queue \n' % (GTIN_in, api_status_code))
                # as this is not a proper API response the number of checked is set 1 lower
                checked = checked - 1
            else:
                log.write('%s %s %s \n' % (GTIN_in, api_status_code, json.dumps(response.text)))

        sec_req = round((time.time() - starttime_req), 2)

        if api_status_code not in range(400, 600):
            response_times.append(sec_req)

        return

    """Start of main program"""
    userstr = credentials.login['email'] + ':' + credentials.login['api_key']

    usrPass = base64.b64encode(userstr.encode())

    headers = {'Authorization': "Basic %s" % str(usrPass)[2:-1]}

    gtins_in = []
    gtins = []
    response_times = []

    gtins_in_input = 0
    checked = 0
    responses_batch = 0
    statistics = {mess_key: 0 for mess_key in list(messages.languages[config.output_language])}

    starttime = time.time()
    timestr = time.strftime("%Y%m%d_%H%M%S")

    # for the sample file no date-time stamp is used
    if config.input_file == "sample_gtins.txt":
        timestr = "yyyymmdd_hhmmss"

    if not os.path.exists('input'):
        os.makedirs('input')

    if not os.path.exists('output'):
        os.makedirs('output')

    input_folder = Path("./input/")
    output_folder = Path("./output/")
    output_file = config.input_file.split(".")

    # copy gtins.txt to input directory for initial set up
    if not os.path.isfile('./input/sample_gtins.txt') and os.path.isfile('./sample_gtins.txt'):
        shutil.copy2('./sample_gtins.txt', './input/')

    output_to_open = "%s_check_%s.csv" % (output_file[0], timestr)
    output_invalid_gtins = "%s_check_invalid_%s.csv" % (output_file[0], timestr)
    log_to_open = "%s_check_%s.log" % (output_file[0], timestr)
    input_to_save = "%s_input_%s.txt" % (output_file[0], timestr)

    output = open(str(output_folder / output_to_open), "w", encoding='utf-8')
    output_inval = open(str(output_folder / output_invalid_gtins), "w", encoding='utf-8')
    log = open(str(output_folder / log_to_open), "w", encoding='utf-8')
    saved_input = open(str(output_folder / input_to_save), "w", encoding='utf-8')
    active_gtins = open(str("active_gtins.txt"), "w", encoding='utf-8')

    # Write CSV Header
    output.write("GTIN|STATUS|MESSAGEID|REASON|GCP_COMPANY|COMPANY|LANGUAGE \n")
    output_inval.write("GTIN|STATUS|MESSAGEID|REASON|GCP_COMPANY|COMPANY|LANGUAGE \n")

    if not os.path.isfile('./input/' + config.input_file):
        print("The input file %s is missing in directory input. \n" % config.input_file)
        log.write("The input file %s is missing in directory input. \n" % config.input_file)
        exit()

    if config.output_language in messages.languages:
        lang = config.output_language
    else:
        lang = 'en'
        print("Unknown language. Available languages are:")
        log.write("Unknown language. Available languages are: \n")
        for lang in messages.languages:
            print(lang)
            log.write("- %s\n" % lang)
        print()
        print("Output language set to English. \n")
        log.write("Output Language set to English. \n")
        print("You can update this setting in the file config.py. \n")
        log.write("You can update this setting in the file config.py. \n")
        log.write("\n")

    # Generate list of GTINS
    with open(str(input_folder / config.input_file), "r") as myfile:
        for line in myfile:
            gtin = line.replace('\n', '')
            gtins_in.append(gtin)

    # Removing duplicates
    gtins = list(dict.fromkeys(gtins_in))
    if (len(gtins_in)-len(gtins)) != 0:
        print("\n%s duplicate(s) removed.\n" % (len(gtins_in)-len(gtins)))
        log.write("\n%s duplicate(s) removed.\n" % (len(gtins_in)-len(gtins)))
    gtins_in.clear()

    # Instantiate a thread pool with n worker threads
    pool = ThreadPool(config.poolsize)

    # Add the jobs in batches to the thread pool.

    def chunks(l, n):
        # For item i in a range that is a length of l,
        for i in range(0, len(l), n):
            # Create an index range for l of n items:
            yield l[i:i+n]

    # Create a list that from the results of the function chunks:
    batches = list(chunks(gtins, config.batchsize))

    print("Processing of file %s started. \n" % (config.input_file))
    print("Dataset of %s GTINS split in %s batch(es) of %s GTINS.\n" % (len(gtins), len(batches), min(config.batchsize, len(gtins))))

    if config.start_with_batch != 0:
        print('Starting with batch: %s \n' % config.start_with_batch)

    # Jobs can be added via map() or add_task()
    # pool.map(check, gtins[cnt])

    for i in range(0, len(batches)):
        starttime_batch = time.time()
        responses_batch = 0
        pool.map(check, batches[i])
        # Demonstrates that the main process waited for threads to complete
        pool.wait_completion()
        sec_job = round((time.time() - starttime))
        sec_batch = round((time.time() - starttime_batch))
        print("Finished batch %s: %s GTINS after %s (%s responses in %s seconds, %s per second). \n" % (i, len(batches[i]), str(
            datetime.timedelta(seconds=sec_job)), responses_batch, sec_batch, round(responses_batch/max(sec_batch, 1), 1)))
        log.write("Finished batch %s: %s GTINS after %s (%s responses in %s seconds, %s per second). \n" %
                  (i, len(batches[i]), str(datetime.timedelta(seconds=sec_job)), responses_batch, sec_batch, round(responses_batch/max(sec_batch, 1), 1)))

    gtins_in_input = len(gtins)

    sec_job = round((time.time() - starttime))

    print("All done.\n")
    print("Unique GTINS in input file: %s\n" % gtins_in_input)
    print("GTINS checked: %s\n" % checked)
    print("API requests without result: %s\n" % (gtins_in_input - checked))
    print("Time: %s\n" % str(datetime.timedelta(seconds=sec_job)))
    if checked > 0:
        print("Checks per second: %s\n" % round(checked/max(sec_job, 1), 1))
        print("Minimum response time per request: %s seconds\n" % min(response_times))
        print("Average response time per request: %s seconds\n" % round(mean(response_times), 2))
        print("Median response time per request: %s seconds\n" % round(median(response_times), 2))
        print("Maximum response time per request: %s seconds\n" % max(response_times))

    print("\nStatistics")
    print("----------")
    for key in sorted(statistics.keys()):
        if statistics[key] == 0:
            statistics[key] = '-'
        print(str(statistics[key]).rjust(len(str(gtins_in_input)), ' '), key, messages.languages[config.output_language][key])
    print("\n")

    log.write('\n')
    log.write("Pool size: %s\n" % config.poolsize)
    log.write("Batchsize: %s\n" % config.batchsize)
    log.write("Unique GTINS in input file: %s\n" % gtins_in_input)
    log.write("GTINS checked: %s\n" % checked)
    log.write("API requests without result: %s\n" % (gtins_in_input - checked))
    log.write("Time: %s\n" % str(datetime.timedelta(seconds=sec_job)))
    if checked > 0:
        log.write("Checks per second: %s\n" % round(checked / max(sec_job, 1), 1))
        log.write("Minimum response time per request: %s seconds\n" % min(response_times))
        log.write("Average response time per request: %s seconds\n" % round(mean(response_times), 2))
        log.write("Median response time per request: %s seconds\n" % round(median(response_times), 2))
        log.write("Maximum response time per request: %s seconds\n" % max(response_times))

    log.write("\nStatistics \n")
    log.write("----------\n")
    for key in sorted(statistics.keys()):
        if statistics[key] == 0:
            statistics[key] = '-'
        log.write("%s %s %s \n" % (str(statistics[key]).rjust(len(str(gtins_in_input)), ' '), key, messages.languages[config.output_language][key]))

    # Save all unique GTINS in file
    for cntr in range(0, len(gtins)):
        saved_input.write("%s\n" % gtins[cntr])

    output.close()
    output_inval.close()
    myfile.close()
    log.close()
    active_gtins.close()
    saved_input.close()
