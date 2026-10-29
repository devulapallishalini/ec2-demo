# EC2 web server in the public subnet from vpc.tf.

# Newest Amazon-owned image matching the image tag.
data "aws_ami" "selected" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = [var.ami_name_pattern]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "deployer" {
  key_name   = "${local.name_prefix}-key"
  public_key = file(pathexpand(var.public_key_path))
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.selected.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]
  key_name               = aws_key_pair.deployer.key_name

  # Serve the booking app with nginx and Grafana directly; no container runtime is needed.
  user_data                   = <<-EOF
    #!/bin/bash
    set -euo pipefail
    cat > /etc/yum.repos.d/grafana.repo <<'GRAFANA_REPO'
    [grafana]
    name=grafana
    baseurl=https://rpm.grafana.com
    enabled=1
    gpgcheck=1
    repo_gpgcheck=1
    gpgkey=https://rpm.grafana.com/gpg.key
    sslverify=1
    sslcacert=/etc/pki/tls/certs/ca-bundle.crt
    GRAFANA_REPO
    dnf install -y nginx grafana python3 python3-pip
    python3 -m venv /opt/booking-app-venv
    /opt/booking-app-venv/bin/python -m pip install --no-cache-dir psutil
    install -d -m 0755 /opt/booking-monitor /etc/prometheus /etc/grafana/provisioning/datasources /etc/grafana/provisioning/dashboards /var/lib/grafana/dashboards
    echo '${base64encode(file("${path.module}/monitoring/system_monitor.py"))}' | base64 -d > /opt/booking-monitor/system_monitor.py
    echo '${base64encode(file("${path.module}/monitoring/system-monitor.service"))}' | base64 -d > /etc/systemd/system/system-monitor.service
    echo '${base64encode(file("${path.module}/monitoring/prometheus.yml"))}' | base64 -d > /etc/prometheus/prometheus.yml
    echo '${base64encode(file("${path.module}/monitoring/prometheus.service"))}' | base64 -d > /etc/systemd/system/prometheus.service
    echo '${base64encode(file("${path.module}/monitoring/grafana-datasource.yml"))}' | base64 -d > /etc/grafana/provisioning/datasources/prometheus.yml
    echo '${base64encode(file("${path.module}/monitoring/grafana-dashboard-provider.yml"))}' | base64 -d > /etc/grafana/provisioning/dashboards/booking-app.yml
    echo '${base64encode(file("${path.module}/monitoring/grafana-dashboard.json"))}' | base64 -d > /var/lib/grafana/dashboards/booking-system-health.json
    chown -R grafana:grafana /etc/grafana/provisioning /var/lib/grafana/dashboards
    id prometheus >/dev/null 2>&1 || useradd --system --no-create-home --shell /sbin/nologin prometheus
    chown -R prometheus:prometheus /etc/prometheus
    install -d -o prometheus -g prometheus /var/lib/prometheus
    prometheus_version="3.5.0"
    curl --fail --location --silent --show-error --retry 5 "https://github.com/prometheus/prometheus/releases/download/v$prometheus_version/prometheus-$prometheus_version.linux-amd64.tar.gz" -o /tmp/prometheus.tar.gz
    tar -xzf /tmp/prometheus.tar.gz -C /tmp
    install -m 0755 "/tmp/prometheus-$prometheus_version.linux-amd64/prometheus" /usr/local/bin/prometheus
    app_url="https://raw.githubusercontent.com/devulapallishalini/booking-app/main"
    curl --fail --location --silent --show-error --retry 5 "$app_url/index.html" -o /usr/share/nginx/html/index.html
    curl --fail --location --silent --show-error --retry 5 "$app_url/styles.css" -o /usr/share/nginx/html/styles.css
    curl --fail --location --silent --show-error --retry 5 "$app_url/app.js" -o /usr/share/nginx/html/app.js
    systemctl enable --now nginx
    systemctl daemon-reload
    systemctl enable --now prometheus system-monitor
    systemctl enable --now grafana-server
  EOF
  user_data_replace_on_change = true

  tags = {
    Name = "${local.name_prefix}-web"
  }
}
