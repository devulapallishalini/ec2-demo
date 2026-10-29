output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_id" {
  value = aws_subnet.public.id
}

output "web_sg_id" {
  value = aws_security_group.web.id
}

output "instance_id" {
  value = aws_instance.web.id
}

output "ami_id" {
  value = aws_instance.web.ami
}

output "public_ip" {
  value = aws_instance.web.public_ip
}

output "web_url" {
  value = "http://${aws_instance.web.public_ip}"
}

output "grafana_url" {
  value = "http://${aws_instance.web.public_ip}:3000"
}

output "ssh_command" {
  value = "ssh -i ~/firstserver ec2-user@${aws_instance.web.public_ip}"
}
