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

### 5) Clone the repository

#### Graph Engine repository
https://github.com/Microsoft/GraphEngine

- Make sure to run "graph/YYYY-MM-DD/samples/CreateFunctions.usql" first before running scripts of Academic Knowledge Analytics.

#### Academic Knowledge Analytics repository
https://github.com/Azure-Samples/academic-knowledge-analytics-visualization
