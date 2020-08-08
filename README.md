# General Information
This repository provides code to help researchers collect information regarding securities class actions from Stanford Class Action Clearinghouse (SCAC) (http://securities.stanford.edu). The code supplements "Measuring Accounting Fraud And Irregularities Using Public And Private Enforcement" (Donelson, Kartpanis, McInnis, and Yust 2020) available at https://sites.google.com/site/christopheryust/research.

# Code Related Information
The code initially loops over the filings list provided by stanford on http://securities.stanford.edu/filings.html. Once the information is collected, it is the output in 
an excel file named "filings_list.xlsx". The code then proceeds to to loop over individual case filings and collects info regarding: 1) the status and first identified complaint (FIC), 2) details from the reference complaint (REF) and 3) company related information as provided by SCAC. Once the information is collected, three more excel files are output: 1) fic_info.xlsx, 2) ref_info.xlsx, and 3) comp_info.xlsx.

The files can be linked to each other based on the "Link" identifier provided in each file. There should be a one-to-one match across all the files. In case that is not the case, 
then the code did not execute correctly or there were connectivitiy issues to Stanford's website. The code tries to capture instances where the response code from stanford indicates
it was unsuccessful and presents the number of such instances at the end. If the number is not equal to 0, you can either try running the code again or collect the data from the
remaining links manually.

In an attempt not to overload stanford's website, a sleep of 10 seconds between page requests is imposed.

Note: You have to define the output location on line 47.
