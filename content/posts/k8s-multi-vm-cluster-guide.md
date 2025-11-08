---
title: 多台虚拟机搭建 k8s 集群
date: '2022-11-12T15:42:35+08:00'
slug: k8s-multi-vm-cluster-guide
draft: true
author: bruce
---

要上手体验 k8s，除了 minikube，还可以用虚拟机自己搭建

此文记录 debian 9 搭建 k8s 集群的过程，使用 kubeadm

使用这套搭建方法需要有代理，kubeadm 安装集群时需要连**外网**

## 创建 debian 9 虚拟机

为了方便创建多个虚拟机以及设置，采用 vagrant 进行安装

首先创建目录

```bash
mkdir -p debian-vms
```

然后进入目录创建 Vagrantfile 配置文件

```bash
vim Vagrantfile
```

内容

```ruby
# 此处定义 3 台虚拟机，ip 依次为 30 31 32
nodes = {
    'dev' => [3, 30],
}

Vagrant.configure("2") do |config|
    config.vm.box = "ubuntu/xenial64"
    config.disksize.size = '40GB'

    group_master = Array.new
    group_vagrant = Array.new
    nodes.each do |prefix, (count, ip_start)| 
        count.times do |i|
            hostname = "%s-%02d" % [prefix, (ip_start + i)]
            if group_master.length == 0
                group_master.push(hostname)
            end
            group_vagrant.push(hostname)

            config.vm.provider "virtualbox" do |vb|
                vb.memory = "2048"
                vb.cpus = 2
                vb.customize ["modifyvm", :id, "--audio", "none"]
            end

            config.vm.define "#{hostname}" do |box|
                box.vm.hostname = "#{hostname}"
            end
        end
    end
    config.vm.provision :ansible do |ansible|
        ansible.playbook = "bootstrap.yml"
        ansible.tags = "vagrant"
        ansible.compatibility_mode = "2.0"
        ansible.groups = {
            "vagrant" => group_vagrant,
            "all_groups:children" => ["vagrant"],
        }
    end
end
```

创建好 Vagrantfile 后，启动虚拟机，由于设定了3台，需要打开3个终端页面，分别输入

## 安装 docker

## 安装 kubeadm kubectl 等

## 初始化 kubeadm

### 设置代理

参考这篇 [docker proxy](https://www.jianshu.com/p/26d0ebd86673)

执行 `kubdadm init`，有以下输出:

```bash
[init] Using Kubernetes version: v1.20.2
[preflight] Running pre-flight checks
    [WARNING IsDockerSystemdCheck]: detected "cgroupfs" as the Docker cgroup driver. The recommended driver is "systemd". Please follow the guide at https://kubernetes.io/docs/setup/cri/
    [WARNING SystemVerification]: missing optional cgroups: hugetlb
[preflight] Pulling images required for setting up a Kubernetes cluster
[preflight] This might take a minute or two, depending on the speed of your internet connection
[preflight] You can also perform this action in beforehand using 'kubeadm config images pull'
[certs] Using certificateDir folder "/etc/kubernetes/pki"
[certs] Generating "ca" certificate and key
[certs] Generating "apiserver" certificate and key
[certs] apiserver serving cert is signed for DNS names [deb9-k8s-master kubernetes kubernetes.default kubernetes.default.svc kubernetes.default.svc.cluster.local] and IPs [10.96.0.1 192.168.1.35]
[certs] Generating "apiserver-kubelet-client" certificate and key
[certs] Generating "front-proxy-ca" certificate and key
[certs] Generating "front-proxy-client" certificate and key
[certs] Generating "etcd/ca" certificate and key
[certs] Generating "etcd/server" certificate and key
[certs] etcd/server serving cert is signed for DNS names [deb9-k8s-master localhost] and IPs [192.168.1.35 127.0.0.1 ::1]
[certs] Generating "etcd/peer" certificate and key
[certs] etcd/peer serving cert is signed for DNS names [deb9-k8s-master localhost] and IPs [192.168.1.35 127.0.0.1 ::1]
[certs] Generating "etcd/healthcheck-client" certificate and key
[certs] Generating "apiserver-etcd-client" certificate and key
[certs] Generating "sa" key and public key
[kubeconfig] Using kubeconfig folder "/etc/kubernetes"
[kubeconfig] Writing "admin.conf" kubeconfig file
[kubeconfig] Writing "kubelet.conf" kubeconfig file
[kubeconfig] Writing "controller-manager.conf" kubeconfig file
[kubeconfig] Writing "scheduler.conf" kubeconfig file
[kubelet-start] Writing kubelet environment file with flags to file "/var/lib/kubelet/kubeadm-flags.env"
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/config.yaml"
[kubelet-start] Starting the kubelet
[control-plane] Using manifest folder "/etc/kubernetes/manifests"
[control-plane] Creating static Pod manifest for "kube-apiserver"
[control-plane] Creating static Pod manifest for "kube-controller-manager"
[control-plane] Creating static Pod manifest for "kube-scheduler"
[etcd] Creating static Pod manifest for local etcd in "/etc/kubernetes/manifests"
[wait-control-plane] Waiting for the kubelet to boot up the control plane as static Pods from directory "/etc/kubernetes/manifests". This can take up to 4m0s
[apiclient] All control plane components are healthy after 29.505545 seconds
[upload-config] Storing the configuration used in ConfigMap "kubeadm-config" in the "kube-system" Namespace
[kubelet] Creating a ConfigMap "kubelet-config-1.20" in namespace kube-system with the configuration for the kubelets in the cluster
[upload-certs] Skipping phase. Please see --upload-certs
[mark-control-plane] Marking the node deb9-k8s-master as control-plane by adding the labels "node-role.kubernetes.io/master=''" and "node-role.kubernetes.io/control-plane='' (deprecated)"
[mark-control-plane] Marking the node deb9-k8s-master as control-plane by adding the taints [node-role.kubernetes.io/master:NoSchedule]
[bootstrap-token] Using token: ttp0wk.g32t620e9zb9mcjl
[bootstrap-token] Configuring bootstrap tokens, cluster-info ConfigMap, RBAC Roles
[bootstrap-token] configured RBAC rules to allow Node Bootstrap tokens to get nodes
[bootstrap-token] configured RBAC rules to allow Node Bootstrap tokens to post CSRs in order for nodes to get long term certificate credentials
[bootstrap-token] configured RBAC rules to allow the csrapprover controller automatically approve CSRs from a Node Bootstrap Token
[bootstrap-token] configured RBAC rules to allow certificate rotation for all node client certificates in the cluster
[bootstrap-token] Creating the "cluster-info" ConfigMap in the "kube-public" namespace
[kubelet-finalize] Updating "/etc/kubernetes/kubelet.conf" to point to a rotatable kubelet client certificate and key
[addons] Applied essential addon: CoreDNS
[addons] Applied essential addon: kube-proxy

Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:

  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

Alternatively, if you are the root user, you can run:

  export KUBECONFIG=/etc/kubernetes/admin.conf

You should now deploy a pod network to the cluster.
Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
  https://kubernetes.io/docs/concepts/cluster-administration/addons/

Then you can join any number of worker nodes by running the following on each as root:

kubeadm join 192.168.1.35:6443 --token ttp0wk.g32t620e9zb9mcjl \
    --discovery-token-ca-cert-hash sha256:6d2b75a07534c1cdd2d3ebf518a97d2d4ee254ab30c997723e8e51956b02258c
```

当看到 `kubeadm join ....` 这句出现，就代表集群 master 创建成功了。

在主节点执行 `kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\n')"` 安装 weave-net 网络插件