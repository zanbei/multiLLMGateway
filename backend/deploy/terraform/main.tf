resource "aws_ecr_repository" "my_ecr" {
  name = "t_litellm"
}

resource "null_resource" "build_and_push" {
  provisioner "local-exec" {
    command = <<EOT
      $(aws ecr get-login --no-include-email --region ${var.region})
      docker build -t ${aws_ecr_repository.my_ecr.repository_url}:latest .
      docker push ${aws_ecr_repository.my_ecr.repository_url}:latest
    EOT
  }

  depends_on = [aws_ecr_repository.my_ecr]
}

resource "random_string" "suffix" {
  length  = 4
  special = false
  upper   = false
}

resource "aws_s3_bucket" "config_bucket" {
  bucket = "bedrock-china-${random_string.suffix.result}"
}



resource "aws_s3_bucket_object" "config_file" {
  bucket = aws_s3_bucket.config_bucket.bucket
  key    = "litellm_config.json"
  source = ""
}

module "aws_rds_cluster" {
  source                  = "terraform-aws-modules/rds-aurora/aws"
  name      = "my-aurora-cluster"
  engine                 = "aurora-postgresql"
  engine_mode           = "serverless"
  # availability_zones = 2
  database_name      = "litellm"
  engine_version         = "14.7"
  master_username        = ""
  master_password        = ""
  vpc_id                 = var.vpc_id
  # subnet_ids             = var.subnet_ids
  # security_group_ids     = [var.security_group_id]
  
}



# 创建 IAM 角色
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "ecsTaskExecutionRole-${random_string.suffix.result}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

variable "iam_policy_arns" {
  description = "List of IAM Policy ARNs to attach to the role"
  type        = list(string)
  default     = [
    "arn:aws-cn:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
    "arn:aws-cn:iam::aws:policy/AmazonS3ReadOnlyAccess"
  ]
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  for_each = toset(var.iam_policy_arns)

  policy_arn = each.key
  role       = aws_iam_role.ecs_task_execution_role.name
}


# 创建 ECS 集群
resource "aws_ecs_cluster" "litellm_cluster" {
  name = "litellm-cluster"
}

# 创建 ECS 任务定义
resource "aws_ecs_task_definition" "litellm_task" {
  family                   = "litellm"
  task_role_arn           = aws_iam_role.ecs_task_execution_role.arn
  execution_role_arn      = aws_iam_role.ecs_task_execution_role.arn
  network_mode             = "awsvpc"
  
  container_definitions    = jsonencode([{
    name      = "litellm"
    image     = "${aws_ecr_repository.my_ecr.repository_url}:latest"
    cpu       = 2048
    memory    = 4096
    memoryReservation = 1024
    essential = true

    portMappings = [
      {
        containerPort = 4000
        hostPort     = 4000
        protocol     = "tcp"
      }
    ]

    environment = [
      {
        name  = "GLOBAL_AWS_REGION"
        value = "us-west-2"
      },
      {
        name  = "GLOBAL_AWS_SECRET_ACCESS_KEY"
        value = ""
      },
      {
        name  = "GLOBAL_AWS_ACCESS_KEY_ID"
        value = ""
      },
      {
        name  = "LITELLM_CONFIG_BUCKET_OBJECT_KEY"
        value = "litellm_config.yaml"
      },
      {
        name  = "AWS_DEFAULT_REGION"
        value = "cn-northwest-1"
      },
      {
        name  = "LITELLM_CONFIG_BUCKET_NAME"
        value = "bedrock-china"
      },
      {
        name  = "LITELLM_LOG"
        value = "DEBUG"
      },
      {
        name  = "DEEPSEEK_KEY"
        value = ""
      },
      {
        name  = "DATA_BASE_URL"
        value = ""
      }
    ]

    logConfiguration = {
      logDriver = "awslogs",
      options   = {
        awslogs-group         = "/ecs/litellm",
        awslogs-region        = var.region,
        awslogs-stream-prefix = "ecs",
        mode                 = "non-blocking",
        max-buffer-size      = "25m",
        awslogs-create-group  = "true",  
      }
    }
  }])

  requires_compatibilities   = ["FARGATE"]
}

# 创建 ECS 服务
resource "aws_ecs_service" "litellm_service" {
  name            = "litellm-service"
  cluster         = aws_ecs_cluster.litellm_cluster.id
  task_definition  = aws_ecs_task_definition.litellm_task.arn
  desired_count   = 1

  network_configuration {
    subnets          = [var.subnet_ids] 
    security_groups  = [var.security_group_id] 
    assign_public_ip = true
  }
}
