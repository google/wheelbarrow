Introduction:
Wheelbarrow is a framework for automated security analysis of Linux packages. 

It is motivated by wanting to inspect packages that are available in the 
Linux software repositories and annotate their security properties. Thus 
getting us a better understanding of the security implications of these.

Summary of functionality:
* Create an on-going pipeline to examine and annotate security properties 
  on packages available in the upstream Ubuntu repositories.
* Annotate the security properties of packages available.

How it works:
Given a list of application packages, Wheelbarrow spawns virtual machines 
(VMs) in order to examine each package. 

Analyses runs inside a VM in order to isolate applications under test from 
the analysis host.  This also enables easily reverting to a sane, controlled 
execution environment. A broker inside the VM triggers events (package 
extraction, installation, starting services, etc.) and gathers data after each 
of these events. Several analyses are included, but the project is designed 
to be easily extensible to other analyses and also to other package 
management systems.

See the INSTALL file to get started.

