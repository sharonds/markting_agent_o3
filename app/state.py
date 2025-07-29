from dataclasses import dataclass, field
from typing import List, Dict, Any
@dataclass
class Artifact: path:str; kind:str; summary:str
@dataclass
class Task:
    id:str; role:str; goal:str
    inputs:Dict[str,Any]=field(default_factory=dict)
    artifacts:List[Artifact]=field(default_factory=list)
    status:str="queued"
@dataclass
class ProjectState:
    compass_meta:dict; compass_body:str; intake:dict
    tasks:List[Task]=field(default_factory=list)
    artifacts:List[Artifact]=field(default_factory=list)
