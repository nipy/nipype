class NipypeError(Exception):
    pass


class EngineError(Exception):
    pass


class PipelineError(NipypeError):
    pass


class NodeError(PipelineError):
    pass


class WorkflowError(NodeError):
    pass


class MappingError(NodeError):
    pass


class JoinError(NodeError):
    pass


class InterfaceError(NipypeError):
    pass
