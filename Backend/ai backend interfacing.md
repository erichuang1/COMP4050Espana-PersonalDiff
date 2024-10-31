# AI & Backend Interfacing

To allow the job subsystem to properly call functions from the AI packages,
there needs to be a number of functions that follow certain requirements.

## Concepts
For future-proofing, the job subsystem is built with the concept of there
being a number of AI 'instances' that can work on jobs. There must be at least
1 'instance' (and, for the time being, we are assuming there is only one instance),
but there may be more. As such, when the subsystem tries to interact with the AI subsystem, it will
pass an instanceID for its queries.

## Functions
```py
	get_job_status(instance:int)->int
```
Checks on the status of a given instance, returning an int code for whether or not
that instance has finished generating for a provided job, is still generating, or has 
no work to do.

The int codes are arbitrary but right now, the assumed codes are:
- -1 	The instance is currently generating.
- 1		The instance has completed generating.
- 0 	The instance is not currently in use.

```py
	submit_job(job:_SubsystemJob, instance: int)->int
```
Submits a job to a given instance by the instance ID. If needed, a file type can be provided that
corresponds to the submission, or it can be fetched manually by referncing the database and file_management.py.

Returns an int code for the status after execution (0 = success, -1 = fail).

```py
	retrieve_job(instance: int)->???
```
Retrieves a completed job (file) from a completed instance. Returns `None` if the instance is not done.
Please let Harris know semantics about files to be returned.

## Notes
You can assume that there is only one instance and ignore instance IDs if there is only one instance. 
Instance IDs will still be passed.

It is preferable that the AI subsystem will not wait until the job is done as this holds up the entire backend.
The job subsystem runs intermittently (i.e. once a second). If this cannot work please let Harris know.


Please let Harris know if there are any questions or specifics needed.
