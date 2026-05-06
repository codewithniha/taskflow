pipeline {
    agent any

    environment {
        APP_IMAGE     = "taskflow-app"
        APP_CONTAINER = "taskflow-running-app"
        APP_PORT      = "5000"
        FALLBACK_EMAIL = "qasimalik@gmail.com"
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
                sh "docker build -t ${APP_IMAGE} -f Dockerfile.app ."
                sh "docker stop  ${APP_CONTAINER} 2>/dev/null || true"
                sh "docker rm    ${APP_CONTAINER} 2>/dev/null || true"
                sh """
                    docker run -d \
                        --name ${APP_CONTAINER} \
                        -p ${APP_PORT}:5000 \
                        ${APP_IMAGE}
                """
                // Wait for Flask to be ready
                sh """
                    for i in \$(seq 1 20); do
                        if curl -sf http://localhost:${APP_PORT}/login; then
                            echo "App is up!"; break
                        fi
                        sleep 3
                    done
                """
            }
        }

        stage('Run Selenium Tests') {
            steps {
                // Install dependencies directly on EC2
                sh 'pip install -r requirements.txt --break-system-packages'

                // Run tests directly — no Docker needed here
                sh """
                    APP_URL=http://localhost:${APP_PORT} \
                    pytest test_taskflow.py -v \
                           --tb=short \
                           --junit-xml=test-results/results.xml
                """
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
                    script: 'git log -1 --format="%ae" 2>/dev/null || echo ""',
                    returnStdout: true
                ).trim()

                def recipients = committerEmail ?
                    "${committerEmail}, ${env.FALLBACK_EMAIL}" :
                    env.FALLBACK_EMAIL

                def buildStatus = currentBuild.currentResult
                def statusIcon  = buildStatus == 'SUCCESS' ? '✅' : '❌'

                emailext(
                    to: recipients,
                    subject: "${statusIcon} TaskFlow [${buildStatus}] — Build #${env.BUILD_NUMBER}",
                    body: """
Hello,

TaskFlow pipeline finished.

Status      : ${buildStatus}
Build       : #${env.BUILD_NUMBER}
Commit      : ${env.GIT_COMMIT?.take(10) ?: 'N/A'}
Build URL   : ${env.BUILD_URL}

Deployment  : http://<YOUR_EC2_IP>:${APP_PORT}
Console     : ${env.BUILD_URL}console
                    """,
                    attachLog: true,
                    attachmentsPattern: 'test-results/results.xml'
                )
            }
            // Clean up app image only (container stays running = app stays deployed)
            sh "docker rmi ${APP_IMAGE} 2>/dev/null || true"
        }
    }
}
