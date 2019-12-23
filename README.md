## A Simple SDN Controller Based on Ryu and Mininet

**This is the second optional project of the final projects for CS305 Computer Network, SUSTech.**

### Project Details

See :[Project Details](./project_requirement/proj_sdn.pdf)

### Environment

The environment establishment requires a Virtual Machine. Vagrant on Ubuntu 16.04 is recommend. For details about environment establish, see: [Tutorial Establishment](./project_requirement/SDN_project-Tutorial_on_Environment_Set-Up.pdf)

### Usage

Use

```bash
sh startup_ryu.sh
```

to initiate Ryu, then use

```bash
python run_mininet.py assign1
```

to run `assign1` network. Some template networks are already provided in [run_mininet.py](https://github.com/WangberlinT/sdn_project/blob/975f289fbb55e5ff2377b7a96c55d905683cfacf/run_mininet.py#L112).

Assign1:

![img_assign1](./project_requirement/image_assign1.png)

Result:

![img_result1](./project_requirement/img_result1.png)

