import { useMemo, useState } from "react"
import panel from "@/data/panel.json"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"

type Row = {
  city: string
  state: string
  year: number
  seat: string
  role: string | null
  person: string | null
  status: string
  confidence: string | null
  url: string | null
}

const rows = panel as Row[]
const YEARS = ["2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"]

const cities = [...new Set(rows.map((r) => `${r.city}|${r.state}`))]
  .map((key) => {
    const [city, state] = key.split("|")
    return { key, label: `${city.replace(/ (city|town|township|borough)$/, "")}, ${state}` }
  })
  .sort((a, b) => a.label.localeCompare(b.label))

function PersonRow({ row }: { row: Row }) {
  return (
    <div className="flex items-center justify-between py-2">
      <div>
        <div className="font-medium">
          {row.person ?? <span className="text-muted-foreground italic">{row.status}</span>}
        </div>
        <div className="text-sm text-muted-foreground">{row.seat}</div>
      </div>
      <div className="flex items-center gap-2">
        {row.confidence && row.confidence !== "high" && (
          <Badge variant="outline">{row.confidence} confidence</Badge>
        )}
        {row.url && (
          <a
            href={row.url}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-muted-foreground underline underline-offset-4 hover:text-foreground"
          >
            source
          </a>
        )}
      </div>
    </div>
  )
}

export default function App() {
  const [cityKey, setCityKey] = useState(cities[0].key)
  const [year, setYear] = useState("2024")

  const { mayors, council } = useMemo(() => {
    const [city, state] = cityKey.split("|")
    const cell = rows.filter(
      (r) => r.city === city && r.state === state && r.year === Number(year),
    )
    return {
      mayors: cell.filter((r) => r.role === "mayor"),
      council: cell.filter(
        (r) =>
          r.role === "council_member" ||
          r.role === "alderman" ||
          (r.role === null && r.status !== "sourced"),
      ),
    }
  }, [cityKey, year])

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Council Counter</h1>
        <p className="text-sm text-muted-foreground">
          Who held every council seat and the mayoralty, 2019–2026.
        </p>
      </div>

      <div className="flex gap-3">
        <Select value={cityKey} onValueChange={setCityKey}>
          <SelectTrigger className="flex-1">
            <SelectValue placeholder="City" />
          </SelectTrigger>
          <SelectContent>
            {cities.map((c) => (
              <SelectItem key={c.key} value={c.key}>
                {c.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={year} onValueChange={setYear}>
          <SelectTrigger className="w-28">
            <SelectValue placeholder="Year" />
          </SelectTrigger>
          <SelectContent>
            {YEARS.map((y) => (
              <SelectItem key={y} value={y}>
                {y}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Mayor</CardTitle>
        </CardHeader>
        <CardContent>
          {mayors.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No mayor — the council elects a presiding officer.
            </p>
          ) : (
            mayors.map((r, i) => <PersonRow key={i} row={r} />)
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>City Council</CardTitle>
        </CardHeader>
        <CardContent>
          {council.map((r, i) => (
            <div key={i}>
              {i > 0 && <Separator />}
              <PersonRow row={r} />
            </div>
          ))}
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground">
        Two names on one seat in one year means turnover within that year. Data:
        councilcounter panel.
      </p>
    </div>
  )
}
