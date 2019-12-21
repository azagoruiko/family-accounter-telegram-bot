job "bot-job" {
  datacenters = ["home"]
  type        = "service"

  group "bot-group" {
    count = 1

    restart {
      attempts = 10
      interval = "5m"
      delay    = "5s"
      mode     = "delay"
    }

    task "bot-task" {
      driver = "docker"
      env {
        RATES_BUCKET="rates"
        PB_INPUT_BUCKET="pb.archive"
        PB_RAW_BUCKET="raw.pb.statements"
        ALFA_RAW_BUCKET="raw.alfa.statements"
      }
      template {
        data = <<EOH
TELEGRAM_TOKEN="{{ key "telegram/bot/accounter/token" }}"
OBJECT_STORAGE_ENDPOINT="{{ key "expenses/object/storage/fs.s3a.endpoint" }}"
OBJECT_STORAGE_KEY="{{ key "expenses/object/storage/fs.s3a.access.key" }}"
OBJECT_STORAGE_SECRET="{{ key "expenses/object/storage/fs.s3a.secret.key" }}"
GOALS_BASE_URL="{{ key "telegram/bot/accounter/goals.base.url" }}"
MATCHERS_BASE_URL="{{ key "expenses/service/matcher/base_url" }}"
EOH
        destination = "secrets.env"
        env = true
      }
      config {
        image = "127.0.0.1:9999/docker/accounter-bot:0.0.7"
        args = [
        ]
      }

      resources {
        cpu    = 300
        memory = 700

        network {
          mbits = 10
        }
      }

      service {
        name = "bot-service"
      }
    }
  }
}

