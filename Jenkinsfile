pipeline {
    agent any

    environment {
        // ── Docker image names ────────────────────────────────────────────────
        APP_IMAGE      = "taskflow-app"
        TEST_IMAGE     = "taskflow-test"
        APP_CONTAINER  = "taskflow-running-app"
        APP_PORT       = "5000"

        // ── Docker network so test container can reach app container ──────────
        DOCKER_NETWORK = "taskflow-net"

        // ── Email: who triggered this build ───────────────────────────────────
        // Jenkins sets GIT_COMMITTER_EMAIL automatically from the git commit.
        // We use it as the primary recipient; add a fallback for safety.
        FALLBACK_EMAIL = "qasimalik@gmail.com"
    }

    stages {

        // ── Stage 1: Pull code from GitHub ────────────────────────────────────
        stage('Checkout') {
            steps {
                echo "Checking out code from GitHub..."
                checkout scm
                // Print the committer email so we can see it in logs
                sh 'git log -1 --format="%ae" || true'
            }
        }

        // ── Stage 2: Build & Deploy the application ───────────────────────────
        // Brings up the Flask app in a named container on a Docker network.
        // "Deployment is down initially" means the container does NOT exist
        // before this pipeline runs — the pipeline is what starts it.
        stage('Deploy Application') {
            steps {
                echo "Building application Docker image..."
                sh "docker build -t ${APP_IMAGE} -f Dockerfile.app ."

                echo "Creating Docker network (if not exists)..."
                sh "docker network create ${DOCKER_NETWORK} 2>/dev/null || true"

                echo "Stopping any previous app container..."
                sh "docker stop ${APP_CONTAINER} 2>/dev/null || true"
                sh "docker rm   ${APP_CONTAINER} 2>/dev/null || true"

                echo "Starting application container..."
                sh """
                    docker run -d \
                        --name ${APP_CONTAINER} \
                        --network ${DOCKER_NETWORK} \
                        -p ${APP_PORT}:5000 \
                        ${APP_IMAGE}
                """

                // Wait until Flask is accepting connections before running tests
                echo "Waiting for Flask to be ready..."
                sh """
                    for i in \$(seq 1 20); do
                        if curl -sf http://localhost:${APP_PORT}/login > /dev/null; then
                            echo "App is up!"
                            break
                        fi
                        echo "Attempt \$i — waiting..."
                        sleep 3
                    done
                """
            }
        }

        // ── Stage 3: Build test image & run 20 Selenium tests ─────────────────
        stage('Run Selenium Tests') {
            steps {
                echo "Building test Docker image..."
                sh "docker build -t ${TEST_IMAGE} -f Dockerfile.test ."

                echo "Creating results directory..."
                sh "mkdir -p \${WORKSPACE}/test-results"

                echo "Running 20 Selenium tests inside Docker..."
                // APP_URL uses the container name (Docker DNS on the shared network)
                sh """
                    docker run --rm \
                        --name taskflow-test-runner \
                        --network ${DOCKER_NETWORK} \
                        -e APP_URL=http://${APP_CONTAINER}:5000 \
                        -v \${WORKSPACE}/test-results:/app/test-results \
                        ${TEST_IMAGE}
                """
            }
            // Publish JUnit results even when tests fail so Jenkins shows the report
            post {
                always {
                    junit allowEmptyResults: true,
                          testResults: 'test-results/results.xml'
                }
            }
        }
    }

    // ── Post-pipeline: Email notification ─────────────────────────────────────
    post {
        always {
            script {
                // Determine who pushed (committer email from git)
                def committerEmail = sh(
                    script: 'git log -1 --format="%ae" 2>/dev/null || echo ""',
                    returnStdout: true
                ).trim()

                // Build recipient list: committer + fallback instructor email
                def recipients = committerEmail ?
                    "${committerEmail}, ${env.FALLBACK_EMAIL}" :
                    env.FALLBACK_EMAIL

                // Build a plain-text summary of test results
                def testSummary = ""
                try {
                    def results = junit allowEmptyResults: true,
                                        testResults: 'test-results/results.xml'
                    testSummary = """
Test Results Summary
────────────────────
Total:   ${results.totalCount}
Passed:  ${results.passCount}
Failed:  ${results.failCount}
Skipped: ${results.skipCount}
"""
                } catch (e) {
                    testSummary = "Test results XML not found — check console output."
                }

                def buildStatus = currentBuild.currentResult  // SUCCESS / FAILURE / UNSTABLE
                def statusIcon  = buildStatus == 'SUCCESS' ? '✅' : '❌'

                emailext(
                    to: recipients,
                    subject: "${statusIcon} TaskFlow Pipeline [${buildStatus}] — Build #${env.BUILD_NUMBER}",
                    body: """
Hello,

The TaskFlow Jenkins pipeline has finished for the commit you pushed.

Pipeline Status : ${buildStatus}
Build Number    : #${env.BUILD_NUMBER}
Branch          : ${env.GIT_BRANCH ?: 'main'}
Commit          : ${env.GIT_COMMIT?.take(10) ?: 'N/A'}
Build URL       : ${env.BUILD_URL}

${testSummary}

Deployment URL  : http://${env.DEPLOYMENT_HOST ?: '<EC2_PUBLIC_IP>'}:${APP_PORT}

Please check the full console output for details:
${env.BUILD_URL}console

Regards,
Jenkins CI — TaskFlow
                    """,
                    attachLog: true,
                    compressLog: true,
                    attachmentsPattern: 'test-results/results.xml'
                )

                echo "Email sent to: ${recipients}"
            }

            // Clean up Docker images to save disk space on EC2
            sh "docker rmi ${TEST_IMAGE}  2>/dev/null || true"
            // NOTE: APP_IMAGE and APP_CONTAINER are intentionally left running
            // so the deployment stays live after the pipeline finishes.
        }

        failure {
            echo "Pipeline FAILED. Check the console output above."
        }

        success {
            echo "Pipeline SUCCEEDED. All tests passed and app is deployed."
        }
    }
}
