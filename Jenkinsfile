pipeline {
    // Run on any available Jenkins agent
    agent any

    environment {
        // Give your Docker image a name
        IMAGE_NAME = "taskflow-test-image"
    }

    stages {

        // Stage 1: Get the code from GitHub
        stage('Checkout') {
            steps {
                echo 'Pulling code from GitHub...'
                checkout scm
                // "scm" means: use whatever repo this Jenkinsfile came from
            }
        }

        // Stage 2: Build a Docker image from your Dockerfile
        stage('Build Docker Image') {
            steps {
                echo 'Building Docker image...'
                sh 'docker build -t ${IMAGE_NAME} .'
                // This reads your Dockerfile and creates an image
            }
        }

        // Stage 3: Run the Docker container, which executes the tests
        stage('Run Selenium Tests') {
            steps {
                echo 'Running 20 Selenium tests inside Docker...'
                sh '''
                    docker run --rm \
                        --name taskflow-runner \
                        ${IMAGE_NAME}
                '''
                // --rm means: delete the container after it finishes
            }
        }
    }

    // What to do after the pipeline finishes (pass or fail)
    post {
        success {
            echo 'All tests passed!'
        }
        failure {
            echo 'Some tests failed. Check the console output above.'
        }
        always {
            // Clean up: remove the Docker image to save disk space
            sh 'docker rmi ${IMAGE_NAME} || true'
            echo 'Pipeline finished.'
        }
    }
}