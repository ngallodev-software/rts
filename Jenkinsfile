pipeline {
    agent any

    triggers {
        // Local Git polling detects commits to master; no remote Git service is used.
        pollSCM('H/2 * * * *')
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
        timeout(time: 45, unit: 'MINUTES')
    }

    environment {
        RTS_REPO_DIR       = '/lump/apps/rts'
        PORTFOLIO_REPO_DIR = '/lump/apps/portfolio-site'
        EXTERNAL_URL       = 'https://ngallodev-software.uk/rts/'
        CI                 = 'true'
    }

    stages {
        stage('Checkout master') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/master']],
                    userRemoteConfigs: [[url: "file://${env.RTS_REPO_DIR}"]],
                    extensions: [[$class: 'LocalBranch', localBranch: 'master']]
                ])
                sh 'test "$(git branch --show-current)" = master'
            }
        }

        stage('Install') {
            steps {
                sh 'command -v google-chrome'
                sh 'npm ci --include=dev --no-audit --no-fund --loglevel=error'
                sh 'python3 -m venv .venv'
                sh '.venv/bin/pip install --disable-pip-version-check --no-cache-dir -r requirements.txt'
            }
        }

        stage('Test') {
            steps {
                sh '.venv/bin/python -m unittest discover -s tests -v'
            }
        }

        stage('Build') {
            steps {
                sh 'VITE_BASE_PATH=/rts/ npm run build'
            }
        }

        stage('Browser UI sanity') {
            steps {
                sh 'npx playwright test'
            }
        }

        stage('Publish and deploy') {
            steps {
                script {
                    def commit = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    sh '''
                        test -d "$PORTFOLIO_REPO_DIR"
                        install -d "$PORTFOLIO_REPO_DIR/public/rts"
                        rsync -a --delete dist/ "$PORTFOLIO_REPO_DIR/public/rts/"
                        rsync -a --delete \
                          --exclude '.git/' --exclude '.codebase-memory/' --exclude '.venv/' \
                          --exclude 'node_modules/' --exclude 'dist/' --exclude 'exports/' \
                          "$WORKSPACE/" "$PORTFOLIO_REPO_DIR/rts-export/"
                    '''
                    dir("${env.PORTFOLIO_REPO_DIR}") {
                        sh 'docker compose --profile tunnel --profile rts up --build -d'
                    }
                    currentBuild.description = "RTS ${commit}"
                }
            }
        }

        stage('Proof of life') {
            steps {
                dir("${env.PORTFOLIO_REPO_DIR}") {
                    sh 'docker compose exec -T rts-export python -c "from urllib.request import urlopen; assert urlopen(\'http://127.0.0.1:8791/healthz\').read() == b\'ok\\n\'"'
                    sh 'docker compose exec -T web wget --no-check-certificate -qO- https://web/rts/ | grep -F \'<div id="root">\''
                }
                sh 'curl -sfL --max-time 20 "$EXTERNAL_URL" | grep -F \'<div id="root">\''
            }
        }
    }
}
