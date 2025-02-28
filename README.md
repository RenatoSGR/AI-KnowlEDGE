<a name="readme-top"></a>


<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/ajakupov_microsoft/EdgeAIDoc">
    <img src="https://camo.githubusercontent.com/76e3e75e12f232eb6e23f28c4f6a177a11a3097a36292227d308cb17378fe33c/68747470733a2f2f6172617361746173617967696e2e6769746875622e696f2f6f70656e6c6f676f732f6c6f676f732f73746570732e6a7067" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">Edge AI Doc</h3>

  <p align="center">
  Edge AI Doc is a desktop application built using Electron.js and Python FastAPI to demonstrate the concept of Disconnected Containers.
    <br />
    <a href="https://github.com/ajakupov_microsoft/EdgeAIDoc"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/ajakupov_microsoft/EdgeAIDoc">View Demo</a>
    ·
    <a href="https://github.com/ajakupov_microsoft/EdgeAIDoc/issues">Report Bug</a>
    ·
    <a href="https://github.com/ajakupov_microsoft/EdgeAIDoc/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
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

Containers enable you to run Azure AI services APIs in your own environment, and are great for your specific security and data governance requirements. Disconnected containers enable you to use several of these APIs disconnected from the internet. 


<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [![Python][Python-logo]][Python-url]
* [![Fastapi][Fastapi-logo]][Fastapi-url]
* [![Nodejs][Nodejs-logo]][Nodejs-url]


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these simple example steps.

### Prerequisites

- Node.js
- Python 3.12+
- Docker
- VS Code

### Installation

1. Clone the repository:
    ```git
    git clone https://github.com/Azure-Samples/EdgeAIDoc.git
    cd EdgeAIDoc
    ```

2. Install Docker and pull container:
    ```sh
    docker pull mcr.microsoft.com/azure-cognitive-services/textanalytics/summarization:cpu
    ```
3. Retrieve your Cognitive Services keys and endpoints. You will need the following information
    ```
    AZURE_DOCUMENT_ANALYSIS_ENDPOINT
    AZURE_DOCUMENT_ANALYSIS_KEY
    LANGUAGE_ENDPOINT
    LANGUAGE_KEY
    ```
4. Create a folder on your C:/ drive and name it `ExtractiveModel`
5. Now download the SLMs for the Summarization Service. Start Docker and run the following code in your terminal
    ```sh
    docker run -v C:\ExtractiveModel:/models mcr.microsoft.com/azure-cognitive-services/textanalytics/summarization:cpu downloadModels=ExtractiveSummarization billing=LANGUAGE_ENDPOINT apikey=LANGUAGE_KEY
    ```
3. Set up Python environment and install dependencies:
    ```sh
    cd backend
    python -m venv venv
    venv\Scripts\activate  # On Linux use `source venv/bin/activate`
    pip install -r requirements.txt
    ```

4. Create docker-compose.yml and put the following code:
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

5. Now you can create the container. Simply run the following command.

    ```sh
    cd backend
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Debugging

1. Start the FastAPI backend:
    ```sh
    cd backend
    uvicorn main:app --port 8000 
    ```

2. Start the Streamlit app:
    ```sh
    cd frontend
    streamlit run app.py --server.port=8501 
    ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [ ] Other Containers Integration
- [ ] Other Use Cases Integration
- [ ] Packaging
    - [ ] Cross-platform installation

See the [open issues](https://github.com/ajakupov_microsoft/EdgeAIDoc/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Raoui Lassoued [@rlassoued](https://twitter.com/ajakupov1) [LinkedIn](https://www.linkedin.com/in/raoui-lassoued-07332165/) 

Project Link: [DocEdge](https://github.com/ajakupov_microsoft/EdgeAIDoc)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [The Rookie Developer Blog](https://www.alirookie.com/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
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
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com 
[Python-logo]: https://img.shields.io/badge/python-0769AD?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org
[Django-logo]: https://img.shields.io/badge/django-35495E?style=for-the-badge&logo=django&logoColor=4FC08D
[Django-url]: https://www.djangoproject.com
[Fastapi-logo]: https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi
[Fastapi-url]: https://fastapi.tiangolo.com
[Nodejs-logo]: https://img.shields.io/badge/node.js-339933?style=for-the-badge&logo=Node.js&logoColor=white
[Nodejs-url]: https://nodejs.org/en