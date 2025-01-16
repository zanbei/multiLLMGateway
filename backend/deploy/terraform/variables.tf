variable "region" {
  default     = "cn-northwest-1"
  description = "AWS Region"
}

# variable "db_username" {
#  description = "Database username"
# }

# variable "db_password" {
#  description = "Database password"
#}

variable "vpc_id" {
  default = "vpc-ea63d383"
}

variable "subnet_ids" {
  default = "subnet-de3892b7"
}

variable "security_group_id" {
  default = "sg-d25b83ba"
}

