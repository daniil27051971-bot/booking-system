import { Fragment, useEffect, useState } from "react"
import { Link, useNavigate } from "react-router-dom"

import { getResources } from "../api/resourcesApi"
import { getResourceScheduleGrid } from "../api/bookingsApi"
import "../styles/resources.css"

const days = ["Пн", "Вт", "Ср", "Чт", "Пт"]
const hours = [9, 10, 11, 12, 13, 14, 15, 16, 17]

function getTodayDateString() {
    const today = new Date()
    const offset = today.getTimezoneOffset()
    const localDate = new Date(today.getTime() - offset * 60 * 1000)

    return localDate.toISOString().split("T")[0]
}

function getMonday(dateString) {
    const date = new Date(`${dateString}T00:00:00`)
    const day = date.getDay()

    const diff = day === 0 ? -6 : 1 - day
    date.setDate(date.getDate() + diff)

    const offset = date.getTimezoneOffset()
    const localDate = new Date(date.getTime() - offset * 60 * 1000)

    return localDate.toISOString().split("T")[0]
}

function Resources() {
    const navigate = useNavigate()

    const todayDate = getTodayDateString()

    const [resources, setResources] = useState([])
    const [selectedResource, setSelectedResource] = useState(null)
    const [scheduleGrid, setScheduleGrid] = useState(null)
    const [selectedDate, setSelectedDate] = useState(todayDate)

    const [typeFilter, setTypeFilter] = useState("")
    const [capacityFilter, setCapacityFilter] = useState("")
    const [dateFilter, setDateFilter] = useState("")
    const [startTimeFilter, setStartTimeFilter] = useState("")
    const [endTimeFilter, setEndTimeFilter] = useState("")

    const [appliedFilters, setAppliedFilters] = useState({
        type: "",
        capacity: "",
        date: "",
        startTime: "",
        endTime: ""
    })



    useEffect(() => {
        loadResources()
    }, [])

    async function loadResources() {
        try {
            const data = await getResources()
            const activeResources = data.filter(resource => !resource.is_archived)

            setResources(activeResources)

            if (activeResources.length > 0) {
                setSelectedResource(activeResources[0])
                loadSchedule(activeResources[0].id, todayDate)
            }
        } catch (error) {
            console.log(error)
            alert("Ошибка загрузки ресурсов")
        }
    }

    async function loadSchedule(resourceId, dateValue) {
        try {
            const safeDate = dateValue || getTodayDateString()
            const weekStart = getMonday(safeDate)

            const data = await getResourceScheduleGrid(resourceId, weekStart)

            console.log("Сетка занятости:", data)
            setScheduleGrid(data)
        } catch (error) {
            console.log(error)
            setScheduleGrid(null)
        }
    }

    function handleSelectResource(resource) {
        setSelectedResource(resource)
        loadSchedule(resource.id, selectedDate)
    }

    function handleDateChange(event) {
        const newDate = event.target.value
        const today = getTodayDateString()

        if (newDate < today) {
            alert("Нельзя выбрать прошедшую дату")
            return
        }

        setSelectedDate(newDate)

        if (selectedResource) {
            loadSchedule(selectedResource.id, newDate)
        }
    }

    function getTypeName(typeId) {
        if (typeId === 1) return "Помещение"
        if (typeId === 2) return "Оборудование"
        if (typeId === 3) return "Рабочее место"
        return "Ресурс"
    }

    function formatHour(hour) {
        return `${String(hour).padStart(2, "0")}:00`
    }

    function formatShortDate(dateString) {
    const date = new Date(`${dateString}T00:00:00`)

    const day = String(date.getDate()).padStart(2, "0")
    const month = String(date.getMonth() + 1).padStart(2, "0")

    return `${day}.${month}`
}

    function getBookingForSlot(dayIndex, hour) {
        if (!scheduleGrid?.schedule) return null

        const day = scheduleGrid.schedule[dayIndex]
        if (!day) return null

        const slotStart = new Date(`${day.date}T${String(hour).padStart(2, "0")}:00:00`)
        const slotEnd = new Date(slotStart)
        slotEnd.setHours(slotEnd.getHours() + 1)

        return day.bookings.find(booking => {
            const bookingStart = new Date(booking.start)
            const bookingEnd = new Date(booking.end)

            return bookingStart < slotEnd && bookingEnd > slotStart
        })
    }

    function isPastSlot(dayIndex, hour) {
        const day = scheduleGrid?.schedule?.[dayIndex]

        if (!day) {
            return true
        }

        const slotStart = new Date(`${day.date}T${String(hour).padStart(2, "0")}:00:00`)
        const now = new Date()

        return slotStart <= now
    }

    function handleSlotClick(dayIndex, hour) {
        const booking = getBookingForSlot(dayIndex, hour)
        const isPast = isPastSlot(dayIndex, hour)

        if (booking || isPast) {
            return
        }

        const day = scheduleGrid?.schedule?.[dayIndex]

        if (!day || !selectedResource) {
            return
        }

        navigate(
            `/booking/new/${selectedResource.id}?date=${day.date}&startTime=${formatHour(hour)}&endTime=${formatHour(hour + 1)}`
        )
    }


const filteredResources = resources.filter((resource) => {
    const resourceType = getTypeName(resource.type_id)
    const resourceCapacity = Number(resource.capacity || 0)

    const matchesType =
        appliedFilters.type === "" ||
        resourceType.toLowerCase() === appliedFilters.type.toLowerCase()

    const matchesCapacity =
        appliedFilters.capacity === "" ||
        resourceCapacity >= Number(appliedFilters.capacity)

    return matchesType && matchesCapacity
})

    return (
        <>
    <div className="resources-page">
        <h1 className="resources-title">Ресурсы и занятость</h1>
        </div>
        <div className="filters">
    <select
        value={typeFilter}
        onChange={(e) => setTypeFilter(e.target.value)}
    >
        <option value="">Все типы</option>
       <option value="Помещение">Помещение</option>
       <option value="Оборудование">Оборудование</option>
       <option value="Рабочее место">Рабочее место</option>
    </select>

    <input
        type="number"
        placeholder="Минимальная вместимость"
        value={capacityFilter}
        onChange={(e) => setCapacityFilter(e.target.value)}
    />

    <input
    type="date"
    value={dateFilter}
    min={getTodayDateString()}
    onChange={(e) => setDateFilter(e.target.value)}
/>

    <input
        type="time"
        value={startTimeFilter}
        onChange={(e) => setStartTimeFilter(e.target.value)}
    />

    <input
        type="time"
        value={endTimeFilter}
        onChange={(e) => setEndTimeFilter(e.target.value)}
    />

    <button
        onClick={() => {
            setAppliedFilters({
                type: typeFilter,
                capacity: capacityFilter,
                date: dateFilter,
                startTime: startTimeFilter,
                endTime: endTimeFilter
            })

            if (dateFilter) {
    setSelectedDate(dateFilter)

    if (selectedResource) {
        loadSchedule(selectedResource.id, dateFilter)
    }
}
        }}
    >
        Найти
    </button>

    <button
        onClick={() => {
            setTypeFilter("")
            setCapacityFilter("")
            setDateFilter("")
            setStartTimeFilter("")
            setEndTimeFilter("")

            setAppliedFilters({
                type: "",
                capacity: "",
                date: "",
                startTime: "",
                endTime: ""
            })
        }}
    >
        Сбросить
    </button>
</div>

            <div className="resources-layout">
                <aside className="resources-sidebar">
                    <h2>Каталог ресурсов</h2>

                    {filteredResources.map(resource => (
                        <div
                            key={resource.id}
                            className={
                                selectedResource?.id === resource.id
                                    ? "resource-list-card active"
                                    : "resource-list-card"
                            }
                            onClick={() => handleSelectResource(resource)}
                        >
                            <h3>{resource.name}</h3>
                            <p>Тип: {getTypeName(resource.type_id)}</p>
                            <p>Вместимость: {resource.capacity}</p>
                            <p>Локация: {resource.location}</p>

                            <Link
                                to={`/booking/new/${resource.id}`}
                                onClick={event => event.stopPropagation()}
                            >
                                <button className="book-btn">
                                    Забронировать
                                </button>
                            </Link>
                        </div>
                    ))}
                </aside>

                <main className="schedule-panel">
                    {selectedResource ? (
                        <>
                            <div className="schedule-header">
                                <div>
                                    <h2>
                                        {selectedResource.name} · {selectedResource.capacity} мест
                                    </h2>
                                    <p>Доступность: 09:00–18:00</p>
                                </div>

                                <div className="schedule-actions">
                                    <label>
    Выбрать неделю
    <input
        type="date"
        value={selectedDate}
        min={getTodayDateString()}
        onChange={handleDateChange}
    />
</label>

                                    <Link to={`/booking/new/${selectedResource.id}`}>
                                        <button className="book-btn">
                                            Создать бронь
                                        </button>
                                    </Link>
                                </div>
                            </div>

                            <div className="schedule-grid">
                                <div className="grid-empty"></div>

                                {days.map((day, dayIndex) => {
    const scheduleDay = scheduleGrid?.schedule?.[dayIndex]

    return (
        <div key={day} className="grid-day">
            <span>{day}</span>
            <small>
                {scheduleDay ? formatShortDate(scheduleDay.date) : ""}
            </small>
        </div>
    )
})}

                                {hours.map(hour => (
                                    <Fragment key={hour}>
                                        <div className="grid-time">
                                            {String(hour).padStart(2, "0")}:00
                                        </div>

                                        {days.map((day, dayIndex) => {
                                            const booking = getBookingForSlot(dayIndex, hour)
                                            const isPast = isPastSlot(dayIndex, hour)

                                            return (
                                                <div
                                                    key={`${day}-${hour}`}
                                                    className={
                                                        booking
                                                            ? "grid-slot busy"
                                                            : isPast
                                                                ? "grid-slot past"
                                                                : "grid-slot free"
                                                    }
                                                    onClick={() => handleSlotClick(dayIndex, hour)}
                                                >
                                                    {booking
                                                        ? booking.purpose || "Занято"
                                                        : isPast
                                                            ? "Недоступно"
                                                            : ""}
                                                </div>
                                            )
                                        })}
                                    </Fragment>
                                ))}
                            </div>

                            <div className="schedule-legend">
                                <span><b className="legend busy"></b> Занято</span>
                                <span><b className="legend free"></b> Свободно</span>
                                <span><b className="legend past"></b> Недоступно</span>
                            </div>
                        </>
                    ) : (
                        <p>Ресурсы не найдены</p>
                    )}
                </main>
            </div>
        </>
    )
}

export default Resources