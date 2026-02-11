resource "aws_db_instance" "postgres" {
  identifier        = "affili-ai-db-${var.environment}"
  engine            = "postgres"
  engine_version    = "15.4"
  instance_class    = "db.t3.medium"
  allocated_storage = 20
  storage_type      = "gp3"
  
  username = var.db_username
  password = var.db_password # Injected via TF_VAR_db_password
  
  db_name = "affili_ai"
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  multi_az               = var.environment == "production"
  publicly_accessible    = false
  skip_final_snapshot    = var.environment != "production"
  backup_retention_period = 7
  
  storage_encrypted = true
}

resource "aws_db_subnet_group" "main" {
  name       = "affili-ai-db-subnet-group-${var.environment}"
  subnet_ids = module.vpc.private_subnets
}

# Redis (ElastiCache)
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "affili-ai-redis-${var.environment}"
  engine               = "redis"
  node_type            = "cache.t4g.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "affili-ai-redis-subnet-group-${var.environment}"
  subnet_ids = module.vpc.private_subnets
}
