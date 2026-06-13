terraform {
  backend "s3" {
    endpoint                    = "http://storage.yandexcloud.net"
    bucket                      = "tf-state-cloud-deploy"
    key                         = "infrastructure/terraform.tfstate"
    region                      = "ru-central1"
    skip_region_validation      = true
    skip_credentials_validation = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
  }
}
