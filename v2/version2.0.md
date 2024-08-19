# TaskRep Version 2.0
With the second implementation of the taskrep, the deployment is now being considered through `elastic beanstalk` which can be a single medium for application deployment such as these ones.
Since there is not much provisioning needed for the computation, as most of the rendering of the tasks and the messages that are going to be sent are going through the external `OpenAI` API calls.

A database instance will be attached to the configured environment to read and write into the tasks into the DB
