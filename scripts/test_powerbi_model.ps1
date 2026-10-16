param(
    [Parameter(Mandatory=$true)][string]$ProjectDirectory,
    [Parameter(Mandatory=$true)][string]$TomDirectory
)
# Offline parser check only. Does not execute M/DAX or render/refresh Desktop.
$ErrorActionPreference = 'Stop'
Get-ChildItem -LiteralPath $TomDirectory -Filter '*.dll' |
    Where-Object Name -NotLike '*resources*' |
    ForEach-Object { Add-Type -Path $_.FullName }
$manifest = Get-Content -LiteralPath (Join-Path $ProjectDirectory 'project-manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$folder = Join-Path $ProjectDirectory ($manifest.modelDirectory + '/definition')
$db = [Microsoft.AnalysisServices.Tabular.TmdlSerializer]::DeserializeDatabaseFromFolder($folder)
$fields = 0
$measures = 0
foreach ($table in $db.Model.Tables) {
    $fields += $table.Columns.Count
    $measures += $table.Measures.Count
    foreach ($column in $table.Columns) {
        if ($column.SourceColumn -ne $column.Name) { throw 'Source column mapping differs from generated CSV header.' }
    }
}
if ($fields -ne $manifest.fields -or $measures -ne $manifest.measures -or $db.Model.Tables.Count -ne $manifest.tables) {
    throw 'Model counts do not match project manifest.'
}
@{check='TOM parse';status='passed';tables=$db.Model.Tables.Count;fields=$fields;measures=$measures;relationships=$db.Model.Relationships.Count;desktop_validated=$false} | ConvertTo-Json
