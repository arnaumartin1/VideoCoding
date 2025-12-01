# LAB 1 – Video Coding and Systems

## Exercise 1

To complete the first exercise, we decided to use FastAPI, as it is the recommended tool. First, we created and activated a virtual environment and prepared a requirements file including everything needed, especially FastAPI. To create the API, we made a Python file called first_practice.py. In this file we imported all required libraries, especially FastAPI, and created our API with app = FastAPI(title="FastAPI for Practice 1").

Next, to place the API inside Docker, we had to create a Dockerfile. This Dockerfile builds an image based on Python 3.11 and sets /app as the working directory. It updates system repositories and cleans cache to reduce image size. It then copies the requirements_minimal.txt file and installs the Python dependencies listed there. After that, it copies the entire project into the container. Finally, it defines the default command to run the Uvicorn server, loading the app located in the first_practice module, listening on port 8000, and enabling automatic reload when code changes occur.

We then built the Docker image with docker build -t practice-api . and ran it using docker run. When opening the URL on port 8000, we can see the message defined in our API.

## Exercise 2

To use FFmpeg inside Docker, we modified our Dockerfile by adding the lines that update apt, install ffmpeg without recommendations, and remove cached lists. This allows FFmpeg to run inside the container.

## Exercise 3

For this third exercise, we used AI to adapt the code from the previous seminar. The seminar code was adapted to function as a complete API with FastAPI. Functions that previously executed manually were converted into HTTP endpoints that receive JSON data or uploaded files. To do this, we created Pydantic models (RGB and YUV) that automatically validate received values, ensuring they are integers and within the correct range. The color conversion functions from the seminar were encapsulated into internal services and are now called by endpoints such as /convert/rgb_to_yuv/ and /convert/yuv_to_rgb/, returning JSON responses.

The parts of the seminar using FFmpeg to resize images were also modified to work inside an API. Files are received using UploadFile, saved temporarily in a shared directory (/shared), and processed using the ffmpeg-python library. We also added try/except blocks to catch FFmpeg or execution errors and return an HTTPException with an appropriate message and HTTP status code, making the API more robust.

## Exercise 4

As mentioned in the previous exercise, we needed to create endpoints in the adapted seminar code. Specifically, actions that previously ran locally, such as converting between RGB and YUV or manipulating files with FFmpeg, were turned into FastAPI routes that receive data or files and return the result in JSON format. This allows the operations from Seminar 1 to be executed via HTTP requests, making the code more reusable and accessible from any client.

## Exercise 5

In this exercise, a docker-compose.yml file was created to run two containers and allow collaboration between them. One container runs the FastAPI API and the other runs FFmpeg. A shared volume was defined so both containers can access the same files, allowing the API to save images or videos and the FFmpeg container to process them. Dependencies and environment variables were configured so the API knows which container to use for conversions. In summary, we built an architecture where the API and FFmpeg run in independent containers but are interconnected through docker-compose.

## Conclusions

All these exercises resulted in being able to deploy the API on a port and test the methods created in the previous seminar in a more interactive way. We ensured that all methods work correctly in the API. In Docker Desktop, the output of the resized image used in the second method of the previous seminar is stored and visible.
