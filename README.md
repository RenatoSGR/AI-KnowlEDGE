<a name="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<br />
<div align="center">
  <img src="images/logo_black.png" alt="Logo" width="600">

  <h3 align="center">AIknowlEDGE</h3>
  <p align="center">
    AIknowlEDGE is a desktop application that enables users to seamlessly deploy and manage their disconnected Azure AI services with ease. 
    <br />
    <br />
    <a href="https://www.youtube.com/watch?v=m9Q2RUp-3Vo">
      <img src="https://upload.wikimedia.org/wikipedia/commons/0/09/YouTube_full-color_icon_%282017%29.svg" alt="YouTube logo" width="20" style="vertical-align: middle;" />
      <strong>View Demo</strong>
    </a>
    <br />
    <br />
    <a href="https://learn.microsoft.com/en-us/azure/ai-services/containers/disconnected-container-faq">Explore the docs</a>
    ·
    <a href="https://github.com/Azure-Samples/AI-knowlEDGE/issues">Report Bug</a>
    ·
    <a href="https://github.com/Azure-Samples/AI-knowlEDGE/issues">Request Feature</a>
  </p>
</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot]](https://example.com)

Welcome to the AI-KnowlEDGE project! The goal of this repository is to provide an accelerator that enables users to quickly and efficiently set up and run Azure AI services on a disconnected environment. By following our comprehensive set of instructions and utilizing the provided sample project, users can seamlessly deploy and manage their disconnected services with ease. Our aim is to simplify the setup process, reduce deployment time, and ensure a smooth operational experience for all users.

Azure AI services offer a variety of Docker containers that allow you to utilize the same APIs available in Azure, but on your own premises. By using these containers, you gain the flexibility to position Azure AI services closer to your data, which can be beneficial for compliance, security, or other operational needs. Currently, container support is offered for a limited number of Azure AI services.

Containerization is a method of software distribution where an application or service, along with its dependencies and configuration, is bundled together into a container image. This container image can be deployed on a container host with minimal or no alterations. Containers are isolated from one another and from the underlying operating system, and they have a smaller footprint compared to virtual machines. They can be created from container images for temporary tasks and removed when they are no longer needed.


### Features and Benefits

* **Immutable Infrastructure**: DevOps teams can utilize a consistent and reliable set of known system parameters while remaining adaptable to changes. Containers offer the flexibility to pivot within a stable ecosystem and prevent configuration drift.

* **Control Over Data**: You can determine where your data is processed by Azure AI services, which is crucial if you cannot send data to the cloud but still need access to Azure AI services APIs. This approach supports consistency in hybrid environments across data, management, identity, and security.

* **Control Over Model Updates**: You have the flexibility to version and update models deployed in your solutions as needed.

* **Portable Architecture**: Containers enable the creation of a portable application architecture that can be deployed on Azure, on-premises, and at the edge. They can be deployed directly to Azure Kubernetes Service, Azure Container Instances, or a Kubernetes cluster on Azure Stack. For more details, see Deploy Kubernetes to Azure Stack.

* **High Throughput / Low Latency**: Containers allow Azure AI services to run close to your application logic and data, meeting high throughput and low latency requirements. They do not limit transactions per second (TPS) and can scale both vertically and horizontally to meet demand, given sufficient hardware resources.

* **Scalability**: With the growing popularity of containerization and container orchestration software like Kubernetes, scalability is a key focus. Building on a scalable cluster foundation allows for application development that supports high availability.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With
* [![Azure][Azure-logo]][Azure-url]
* [![Python][Python-logo]][Python-url]
* [![Fastapi][Fastapi-logo]][Fastapi-url]
* [![Docker][Docker-logo]][Docker-url]
* [![Ollama][Ollama-logo]][Ollama-url]
* [![Streamlit][Streamlit-logo]][Streamlit-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

Follow these steps to run the project locally.

### Prerequisites

- Python 3.12+  
- Docker  
- VS Code  
- Ollama  

### Installation

1. Clone the repository:
    ```git
    git clone https://github.com/Azure-Samples/AI-knowlEDGE.git
    cd AI-knowlEDGE
    ```

2. Install Docker and start. Then open the cmd and pull the container by running the following command:
    ```sh
    docker pull mcr.microsoft.com/azure-cognitive-services/textanalytics/summarization:cpu
    ```

3. Get the Azure Cognitive Services keys and endpoints for Azure Document Intelligence and Azure AI Language. Before using Cognitive Services containers in disconnected environments, you must complete a request form and purchase a commitment plan. Next, provision a new resource in the portal. Select the **DC0** option for the Pricing tier to enable disconnected containers, (for Document Intelligence additionally choose a custom, read, or prebuilt commitment tier). 

*Note: For a “semi-disconnected” mode, you can provision a Document Intelligence and Language Resource with the S0 commitment plan, without filling any request form*.

For your convienice, create a txt document and save the keys and endpoint in the following format:

    ```
    AZURE_DOCUMENT_ANALYSIS_ENDPOINT = <document-intelligence-endpoint>
    AZURE_DOCUMENT_ANALYSIS_KEY = <document-intelligence-key>
    LANGUAGE_ENDPOINT = <ai-language-endpoint>
    LANGUAGE_KEY = <ai-language-key>
    ```

4. Create a folder on your C:/ drive named `ExtractiveModel`.

5. Download the SLMs for the Summarization Service. Start Docker and run:
    ```Docker
    docker run -v C:\ExtractiveModel:/models mcr.microsoft.com/azure-cognitive-services/textanalytics/summarization:cpu downloadModels=ExtractiveSummarization billing=LANGUAGE_ENDPOINT apikey=LANGUAGE_KEY
    ```

6. Now open the cloned repo in a command line or VSCode, and set up the Python environment and install project dependencies:
    ```sh
    python -m venv venv
    venv\Scripts\activate  # On Linux use `source venv/bin/activate`
    pip install -r requirements.txt
    ```

7. Create a docker-compose.yml (in the root folder) with the following code:
    ```YAML
    version: "3.9"
    services:
      azure-form-recognizer-read:
        container_name: azure-form-recognizer-read
        image: mcr.microsoft.com/azure-cognitive-services/form-recognizer/read-3.1
        environment:
          - EULA=accept
          - billing=<document-intelligence-endpoint>
          - apiKey=<document-intelligence-key>
        ports:
          - "5000:5000"
        networks:
          - ocrvnet

      textanalytics:
        image: mcr.microsoft.com/azure-cognitive-services/textanalytics/summarization:cpu
        environment:
          - eula=accept
          - rai_terms=accept
          - billing=<language-endoint>
          - apikey=<language-key> 
        volumes:
          - "C:\\ExtractiveModel:/models"
        ports:
          - "5001:5000"

    networks:
      ocrvnet:
        driver: bridge
    ```

8. Create the container by running:
    ```sh
    docker-compose up
    ```

9. Make a .env file:
    ```
    AZURE_DOCUMENT_ANALYSIS_ENDPOINT=http://localhost:5000
    AZURE_DOCUMENT_ANALYSIS_KEY=<document-intelligence-key>
    LANGUAGE_ENDPOINT=http://localhost:5001
    LANGUAGE_KEY=<language-key>
    ```

10. Download Ollama and install at least one SLM and one embedding model:
    ```sh
    ollama pull phi3
    ```
    We also use an embedding model to vectorize document chunks and build a local RAG solution with **ChromaDB**. Thus, additionally, ensure that the required embedding model is installed.
    ```sh
    ollama pull nomic-embed-text
    ```

11. Start the FastAPI backend (from the root folder):
    ```sh
    uvicorn backend.main:app --host 0.0.0.0 --port 8000
    ```
    If you're using VS Code, simply press F5 or go to **Run** > **Start Debugging**. The `launch.json` is already configured.

12. Open another terminal and start the Streamlit frontend:
    ```sh
    streamlit run frontend/app.py --server.port=8501
    ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Debugging and troubleshooting

* If you see the following error```
requests.exceptions.ConnectionError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /get_models/ (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x124209be0>: Failed to establish a new connection: [Errno 61] Connection refused'))``` make sure the FastAPI backend is running. Check the outputs if needed.

* If you're able to start the streamlit app and see the following error message: ```No Ollama models found. Please ensure Ollama is running and models are installed.``` this means you didn't start the ollama application.

* You can also run unit tests from the **tests** folder, for debugging the FastAPI backend.


<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->
## Roadmap

- [ ] Other Containers Integration
  - [ ] Speech service
  - [ ] Translation service
- [ ] Other Use Cases Integration
- [ ] Packaging
  - [ ] Single-click installation
  - [ ] Cross-platform installation

See the [open issues](https://github.com/Azure-Samples/AIknowlEDGE/issues) for proposed features and known issues.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->
## Contributing

Contributions make open source great. We appreciate all contributions.

1. Fork this repo
2. Create a Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more info.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->
## Contact

* Raoui Lassoued [LinkedIn](https://www.linkedin.com/in/raoui-lassoued-07332165/)
* Serge Retkowsky [LinkedIn](https://www.linkedin.com/in/serger/)
* Farid El Attaoui [LinkedIn](https://www.linkedin.com/in/farid-el-attaoui/)
* Alibek Jakupov [@ajakupov1](https://twitter.com/ajakupov1) [LinkedIn](https://www.linkedin.com/in/alibek-jakupov-30305b61/)

Project Link: [AIKnowlEDGE](https://learn.microsoft.com/en-us/azure/ai-services/containers/disconnected-container-faq)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* Microsoft France

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/ajakupov/NewsExplorer.svg?style=for-the-badge
[contributors-url]: https://github.com/ajakupov/NewsExplorer/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/ajakupov/NewsExplorer.svg?style=for-the-badge
[forks-url]: https://github.com/ajakupov/NewsExplorer/network/members
[stars-shield]: https://img.shields.io/github/stars/ajakupov/NewsExplorer.svg?style=for-the-badge
[stars-url]: https://github.com/ajakupov/NewsExplorer/stargazers
[issues-shield]: https://img.shields.io/github/issues/ajakupov/NewsExplorer.svg?style=for-the-badge
[issues-url]: https://github.com/ajakupov/NewsExplorer/issues
[license-shield]: https://img.shields.io/github/license/ajakupov/NewsExplorer.svg?style=for-the-badge
[license-url]: https://github.com/ajakupov/NewsExplorer/blob/main/LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/company/microsoft/
[product-screenshot]: https://learn.microsoft.com/en-us/azure/ai-services/containers/media/container-security.svg
[Python-logo]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[Python-url]: https://www.python.org
[Django-logo]: https://img.shields.io/badge/django-35495E?style=for-the-badge&logo=django&logoColor=4FC08D
[Django-url]: https://www.djangoproject.com
[Fastapi-logo]: https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi
[Fastapi-url]: https://fastapi.tiangolo.com
[Nodejs-logo]: https://img.shields.io/badge/node.js-339933?style=for-the-badge&logo=Node.js&logoColor=white
[Nodejs-url]: https://nodejs.org/en
[Docker-logo]: https://img.shields.io/badge/docker-257bd6?style=for-the-badge&logo=docker&logoColor=white
[Docker-url]: https://www.docker.com
[Streamlit-logo]: https://img.shields.io/badge/-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white
[Streamlit-url]: https://streamlit.io
[Ollama-logo]: https://img.shields.io/badge/-Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white
[Ollama-url]: https://ollama.com
[Azure-logo]: https://img.shields.io/badge/azure-0089D6?style=for-the-badge&logo=azure&logoColor=white
[Azure-url]: https://azure.microsoft.com/en-us/

