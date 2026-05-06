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

Deployment : http://<YOUR_EC2_PUBLIC_IP>:5000
Console    : ${env.BUILD_URL}console
                """,
                attachLog: true,
                attachmentsPattern: 'test-results/results.xml'
            )

            echo "Email sent to committer: ${committerEmail}"
        }

        sh "docker rmi ${APP_IMAGE} 2>/dev/null || true"
    }
}
