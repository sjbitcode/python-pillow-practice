from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int
    job: str = 'SOME-JOB'

    def __post_init__(self):
        self.job = self.job.upper()   
