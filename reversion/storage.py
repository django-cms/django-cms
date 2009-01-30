"""File storage wrapper for version controlled file fields."""


class VersionFileStorageWrapper(object):
    
    """Wrapper for file storage implementations that blocks file deletions."""
    
    def __init__(self, storage):
        """Initializes the VersionFileStorageWrapper."""
        self._storage = storage
        
    def __getattr__(self, name):
        """Proxies storage mechanism to the wrapped implementation."""
        return getattr(self._storage, name)
    
    def delete(self, name):
        """File deletions are blocked for this storage class."""
        pass
