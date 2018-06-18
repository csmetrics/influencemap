*Obsoleted - no longer use GraphEngine (2018-06-18)*

## Running GraphEngine on Windows server + Remote Desktop from Linux

### 0) Remote Desktop from a Linux Computer with RDesktop

- Windows side: Allow remote desktop (through nectar cloud console)
- Linux side: Access using rdesktop command.
```
$ rdesktop -g 1280x1024 server_ip
```

### 1) Windows system settings

#### Change network setting to allow file download

- Click Search, search for Control Panel, and then click Control Panel.
- Click Network and Internet > Internet Options.
- On the Security tab, click Custom level.

#### Allocate external disk space (for storing dataset)
https://www.partitionwizard.com/partitionmagic/new-simple-volume-greyed-out.html

### 2) Install Visual Studio

#### Install Visual Studio

Download: https://www.visualstudio.com/downloads/
- Note: [Visual studio installer failed to download](https://developercommunity.visualstudio.com/content/problem/24328/visual-studio-installer-failed-to-download.html)

#### Install GraphEngine Extention

- Search "Graph Engine" in Visual Studio Extensions and Updates.
- https://www.graphengine.io/download.html
- https://marketplace.visualstudio.com/items?itemName=GraphEngineTeam.GraphEngineVSExtension

### 4) Download dataset from Azure Data Lake Store

#### Install Azure CLI 2.0

- Download and install Azure CLI
https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-windows?view=azure-cli-latest
- open cmd and `$ az login` to log in Azure service.
- Use a web browser to open the page https://aka.ms/devicelogin and enter the code to authenticate.

#### Download Graph using Azure CLI 2.0
https://docs.microsoft.com/en-us/azure/data-lake-store/data-lake-store-get-started-cli-2.0#rename-download-and-delete-data-from-a-data-lake-store-account
```
$ az dls fs download --account academicgraph --source-path /graph/2018-04-24 --destination-path graph/2018-04-24
Alive[##############################                             ] 55.1332%
```

### 5) ENV Path settings

- Open `graph/YYYY-MM-DD/samples/CreateFunctions.usql` in VisualStudio
- Go to Tools > Data Lake > Options and Settings
- Change DataRoot
- Change Path for the AppData Cache as it requires huge disk space.
  - AppData Cache path change: https://answers.microsoft.com/en-us/windows/forum/windows_7-files/change-location-of-temp-files-folder-to-another/19f13330-dde1-404c-aa27-a76c0b450818?auth=1

#### Note

- `graph/YYYY-MM-DD/samples/AcademicGraphSample.usql` requires 9.25GB temporal cache space.


### 6) Run the scripts in graph/YYYY-MM-DD/samples

#### Submit CreateFunctions.usql

- Error Note:
```
The failure might be due to unexpected metadata changes since the script was compiled, recompile the script to resolve.
Completed with 'Error' : 22/05/2018 9:41:24 AM
Execution failed with error 'The failure might be due to unexpected metadata changes since the script was compiled, recompile the script to resolve.'
```
  - Solution: remove all the cache data and rerun.


#### Submit AcademicGraphSample.usql
  - Path Settings
  ```
  DECLARE @graphDir   string = "/graph/2018-04-24/";
DECLARE @affiliationId long = 201448701; // Affiliation Id for University of Washington
DECLARE @OutAffiliationTopAuthors string = "/output/UWTopAuthors.tsv";
```
  - Make sure you have enough space (>9.25GB) in temporal cache directory.
```
Start : 22/05/2018 10:29:59 AM
Initialize : 22/05/2018 10:29:59 AM
GraphParse : 22/05/2018 10:29:59 AM
Run : 22/05/2018 10:29:59 AM
Start 'Root' : 22/05/2018 10:29:59 AM
End 'Root(Success)' : 22/05/2018 10:29:59 AM
Start '1_SV1_Extract' : 22/05/2018 10:29:59 AM
Start '2_SV2_Extract' : 22/05/2018 10:45:30 AM
End '1_SV1_Extract(Success)' : 22/05/2018 10:45:30 AM
Start '3_SV3_Extract' : 22/05/2018 10:51:42 AM
End '2_SV2_Extract(Success)' : 22/05/2018 10:51:42 AM
Start '4_SV4_Combine' : 22/05/2018 10:57:41 AM
End '3_SV3_Extract(Success)' : 22/05/2018 10:57:41 AM
Start '5_SV4_Combine' : 22/05/2018 10:58:41 AM
End '4_SV4_Combine(Success)' : 22/05/2018 10:58:41 AM
End '5_SV4_Combine(Success)' : 22/05/2018 10:58:42 AM
PostExecution : 22/05/2018 10:58:42 AM
Completed with 'Success' : 22/05/2018 10:58:42 AM
Press any key to continue . . .
```

- Result will be stored in output directory.

### 7) Run GraphEngine project

#### Clone the repository

- Graph Engine repository: https://github.com/Microsoft/GraphEngine
