import os.path

KNOWN_ROOTS = ['SDKROOT', 'SOURCE_ROOT', 'DEVELOPER_DIR', 'BUILT_PRODUCTS_DIR']


class TargetInfo:
  def __init__(self, project, target):
    self._project = project
    self._target = target
    self._index_groups()
    self._info = {
      'name': target.name,
      'type': target.productType,
      'buildConfigurations': self._get_configurations(),
      'buildPhases': self._get_phases(),
      'dependencies': self._get_dependencies(),
      'files': self._get_files(),
    }

  def dict(self):
    return self._info

  def obj(self, id):
    return self._project.objects[id]

  def get_buildfile_path(self, key):
    buildfile = self.obj(key)
    if buildfile is None or buildfile['fileRef'] is None: return f"(null) {key}"

    fileref = self.obj(buildfile.fileRef)
    if fileref is None or fileref['path'] is None: return f"(null) {key}"

    return repr(fileref)


  def _index_groups(self):
    self._group_parents = {}
    self._group_paths = {}

    self._group_paths[self._project.rootObject] = ''

    root = self.obj(self._project.rootObject)
    self._group_paths[root.mainGroup] = ''

    for group in self._project.objects.get_objects_in_section('PBXGroup'):
      group_id = group.get_id()
      if group['children'] is not None:
        for child in group.children:
          self._group_parents[child] = group_id
      if group.sourceTree in KNOWN_ROOTS:
        self._group_paths[group_id] = f"$({group.sourceTree})"

  def _get_configurations(self):
    if self._target['buildConfigurationList'] is None: return None

    list = self.obj(self._target.buildConfigurationList)
    if list is None or list['buildConfigurations'] is None: return None

    all_confs = {}
    for ckey in list.buildConfigurations:
      conf = self.obj(ckey)
      if conf is None or conf['name'] is None: continue
      all_confs[conf.name] = {
        'buildSettings': {skey : conf.buildSettings[skey] for skey in conf.buildSettings.get_keys()}
      }
    return all_confs

  def _get_phases(self):
    if self._target['buildPhases'] is None: return None

    all_phases = []
    for pkey in self._target.buildPhases:
      phase = self.obj(pkey)
      if phase is None or phase.isa in ['PBXSourcesBuildPhase', 'PBXResourcesBuildPhase', 'PBXFrameworksBuildPhase']: continue
      phase_info = {
        'name': phase['name'],
        'type': phase.isa,
      }
      if 'PBXShellScriptBuildPhase' == phase.isa:
        phase_info['script'] = phase.shellScript
      elif 'PBXCopyFilesBuildPhase' == phase.isa:
        phase_info['files'] = [self.get_buildfile_path(fkey) for fkey in phase.files]
      all_phases.append(phase_info)
    return all_phases

  def _get_dependencies(self):
    all_dependencies = []

    if self._target['dependencies'] is not None:
      for dkey in self._target.dependencies:
        dep = self.obj(dkey)
        if dep is None: continue
        if 'PBXTargetDependency' == dep.isa:
          dep_target = self.obj(dep.target)
          all_dependencies.append({
            'type': dep.isa,
            'target': dep_target.name,
          })
        else:
          all_dependencies.append({'type':dep.isa})

    if self._target['packageProductDependencies'] is not None:
      for dkey in self._target.packageProductDependencies:
        dep = self.obj(dkey)
        if dep is None: continue
        if 'XCSwiftPackageProductDependency' == dep.isa:
          info = {
            'type': dep.isa,
            'productName': dep['productName'],
          }
          pkg = self.obj(dep.package)
          if pkg is not None:
            info['url'] = pkg['repositoryURL']
          all_dependencies.append(info)
        else:
          all_dependencies.append({'type':dep.isa})

    return all_dependencies

  def _get_files(self):
    if self._target['buildPhases'] is None: return None

    sources = []
    resources = []
    frameworks = []

    for pkey in self._target.buildPhases:
      phase = self.obj(pkey)
      if phase is None or phase['files'] is None: continue

      files = self._resolve_files(phase.files)

      if 'PBXSourcesBuildPhase' == phase.isa:
        sources.extend(files)
      elif 'PBXResourcesBuildPhase' == phase.isa:
        resources.extend(files)
      elif 'PBXFrameworksBuildPhase' == phase.isa:
        frameworks.extend(files)

    sources.sort()
    resources.sort()
    frameworks.sort()

    return {
      'sources': sources,
      'resources': resources,
      'frameworks': frameworks,
    }

  def _resolve_files(self, files):
    for id in files:
      file = self.obj(id)
      if file.isa == 'PBXBuildFile':
        if 'fileRef' in file:
          id = file.fileRef
          file = self.obj(id)
        elif 'productRef' in file:
          id = file.productRef
          file = self.obj(id)
        else:
          yield f"(null) {id}"
          continue
      if file.isa == 'PBXVariantGroup':
        variant_path = self._relative_path(id)
        for child_id in file.children:
          yield self._relative_path(child_id, variant_path)
      elif file.isa == 'XCSwiftPackageProductDependency':
        yield f"{file.productName} (Swift package)"
      else:
        yield self._relative_path(id)

  def _relative_path(self, id, variant_path=None):
    if id in self._group_paths:
      return self._group_paths[id]

    obj = self.obj(id)
    if obj is None:
      return f"(null) {id}"

    if obj.isa not in ['PBXFileReference', 'PBXGroup', 'XCVersionGroup', 'PBXVariantGroup']:
      raise Exception(f"Unknown object {obj.isa}")

    if obj.sourceTree in KNOWN_ROOTS:
      parent_path = f"$({obj.sourceTree})"
    elif obj.sourceTree == '<group>':
      if id in self._group_parents:
        parent_path = self._relative_path(self._group_parents[id])
      elif variant_path is not None:
        parent_path = variant_path
      elif obj.get_parent() == self._project.objects:
        parent_path = ''
      else:
        raise Exception(f"Unknown parent for {id}")
    else:
      raise Exception(f"Unknown source {obj.sourceTree}")

    if 'path' in obj:
      path = os.path.join(parent_path, obj.path)
    else:
      path = parent_path
    path = os.path.normpath(path)

    if 'PBXGroup' == obj.isa:
      self._group_paths[id] = path

    return path
