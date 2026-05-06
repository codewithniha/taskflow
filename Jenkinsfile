pipeline {
    agent any

    environment {
        APP_IMAGE     = "taskflow-app"
        APP_CONTAINER = "taskflow-running-app"
        APP_PORT      = "5000"
    }

    stages {

        stage('Checkout') {
            steps {
                echo "Pulling code from GitHub..."
                checkout scm
            }
        }

        stage('Deploy Application') {
            steps {
                echo "Building app Docker image..."
                sh "docker build -t ${APP_IMAGE} ."

                echo "Stopping any old container..."
                sh "docker stop ${APP_CONTAINER} 2>/dev/null || true"
                sh "docker rm   ${APP_CONTAINER} 2>/dev/null || true"

                echo "Starting app container..."
                sh """
                    docker run -d \
                        --name ${APP_CONTAINER} \
                        -p ${APP_PORT}:5000 \
                        ${APP_IMAGE}
                """

                echo "Waiting for Flask to be ready..."
                sh """
                    for i in \$(seq 1 20); do
                        if curl -sf http://localhost:${APP_PORT}/login > /dev/null; then
                            echo "App is up!"
                            break
                        fi
                        echo "Attempt \$i - waiting..."
                        sleep 3
                    done
                """
            }
        }

        stage('Run Selenium Tests') {
    steps {
        echo "Installing pip and dependencies..."
        sh '''
            # Download pip installer directly — no sudo needed
            curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
            python3 get-pip.py --user
            export PATH=$HOME/.local/bin:$PATH

            # Install project dependencies
            python3 -m pip install -r requirements.txt --user
        '''

        echo "Running tests..."
        sh '''
            export PATH=$HOME/.local/bin:$PATH
            mkdir -p test-results
            APP_URL=http://localhost:5000 \
            python3 -m pytest test_taskflow.py -v \
                   --tb=short \
                   --junit-xml=test-results/results.xml
        '''
    }
    post {
        always {
            junit allowEmptyResults: true,
                  testResults: 'test-results/results.xml'
        }
    }
}
    }

    post {
        always {
            script {
                def committerEmail = sh(
                    script: 'git log -1 --format="%ae"',
                    returnStdout: true
                ).trim()

                def buildStatus = currentBuild.currentResult
                def statusIcon  = buildStatus == 'SUCCESS' ? '✅' : '❌'

                emailext(
                    to: committerEmail,
                    subject: "${statusIcon} TaskFlow [${buildStatus}] — Build #${env.BUILD_NUMBER}",
                    body: """
Hello,

The TaskFlow Jenkins pipeline has finished.

Status     : ${buildStatus}
Build      : #${env.BUILD_NUMBER}
Commit     : ${env.GIT_COMMIT?.take(10) ?: 'N/A'}
Build URL  : ${env.BUILD_URL}

Deployment : http://<YOUR_EC2_PUBLIC_IP>:${APP_PORT}
Console    : ${env.BUILD_URL}console
                    """,
                    attachLog: true,
                    attachmentsPattern: 'test-results/results.xml'
                )

                echo "Email sent to committer: ${committerEmail}"
            }

            sh "docker rmi ${APP_IMAGE} 2>/dev/null || true"
        }

        success {
            echo "Pipeline PASSED. App is live."
        }

        failure {
            echo "Pipeline FAILED. Check console output."
        }
    }
}
