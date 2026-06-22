import { useEffect, useState } from "react"
import { useParams, useSearchParams } from "react-router-dom"

import { getResources } from "../api/resourcesApi"
import { createBooking, getMyBookings } from "../api/bookingsApi"
import "../styles/bookingCreate.css"

function BookingCreate() {
    const { resourceId } = useParams()
    const [searchParams] = useSearchParams()

    const [resources, setResources] = useState([])
    const [bookings, setBookings] = useState([])

    const [selectedResourceId, setSelectedResourceId] = useState(resourceId || "")
const [date, setDate] = useState(searchParams.get("date") || "")
const [startTime, setStartTime] = useState(searchParams.get("startTime") || "")
const [endTime, setEndTime] = useState(searchParams.get("endTime") || "")
const [purpose, setPurpose] = useState("")
    useEffect(() => {
        loadData()
    }, [])

    async function loadData() {
        try {
            const resourcesData = await getResources()
            const bookingsData = await getMyBookings()

            setResources(resourcesData)
            setBookings(bookingsData)

            if (resourceId) {
                setSelectedResourceId(resourceId)
            }
        } catch (error) {
            console.log(error)
            alert("Ошибка загрузки данных")
        }
    }

    function getResourceName(id) {
        const resource = resources.find(item => item.id === Number(id))
        return resource ? resource.name : "Ресурс не найден"
    }

    function formatDate(datetime) {
        return new Date(datetime).toLocaleDateString("ru-RU")
    }

    function formatTime(datetime) {
        return new Date(datetime).toLocaleTimeString("ru-RU", {
            hour: "2-digit",
            minute: "2-digit"
        })
    }

    async function handleSubmit(event) {
        event.preventDefault()

        if (!selectedResourceId) {
            alert("Выберите ресурс")
            return
        }

        if (!date || !startTime || !endTime) {
            alert("Заполните дату, начало и конец брони")
            return
        }

        if (!purpose.trim()) {
            alert("Введите цель брони")
            return
        }

        try {
            await createBooking({
                resource_id: Number(selectedResourceId),
                start_datetime: `${date}T${startTime}:00`,
                end_datetime: `${date}T${endTime}:00`,
                purpose: purpose.trim(),
                seats: 1,
                is_recurring: false,
                series: null
            })

            alert("Бронь успешно создана")

            setDate("")
            setStartTime("")
            setEndTime("")
            setPurpose("")

            const updatedBookings = await getMyBookings()
            setBookings(updatedBookings)
        } catch (error) {
            console.log(error)
            alert(error.response?.data?.detail || "Ошибка создания брони")
        }
    }

    return (
        <div className="booking-page">
            <h1>Создание брони</h1>

            <div className="booking-layout">
                <div className="booking-form-card">
                    <h2>Новое бронирование</h2>

                    <form onSubmit={handleSubmit}>
                        <label>Ресурс</label>
                        <select
                            value={selectedResourceId}
                            onChange={event => setSelectedResourceId(event.target.value)}
                        >
                            <option value="">Выберите ресурс</option>

                            {resources.map(resource => (
                                <option key={resource.id} value={resource.id}>
                                    {resource.name} · {resource.capacity} мест
                                </option>
                            ))}
                        </select>

                        <label>Дата</label>
                        <input
                            type="date"
                            value={date}
                            onChange={event => setDate(event.target.value)}
                        />

                        <div className="time-row">
                            <div>
                                <label>Начало</label>
                                <input
                                    type="time"
                                    value={startTime}
                                    onChange={event => setStartTime(event.target.value)}
                                />
                            </div>

                            <div>
                                <label>Конец</label>
                                <input
                                    type="time"
                                    value={endTime}
                                    onChange={event => setEndTime(event.target.value)}
                                />
                            </div>
                        </div>

                        <label>Цель брони</label>
                        <input
                            type="text"
                            placeholder="Например: командная встреча"
                            value={purpose}
                            onChange={event => setPurpose(event.target.value)}
                        />

                        <button type="submit" className="primary-btn">
                            Забронировать
                        </button>
                    </form>
                </div>

                <div className="my-bookings-preview">
                    <h2>Мои брони</h2>

                    {bookings.length === 0 && (
                        <p>У вас пока нет бронирований</p>
                    )}

                    {bookings.map(booking => (
                        <div key={booking.id} className="mini-booking-card">
                            <h3>{getResourceName(booking.resource_id)}</h3>

                            <p>
                                {formatDate(booking.start_datetime)} ·{" "}
                                {formatTime(booking.start_datetime)}–{formatTime(booking.end_datetime)}
                            </p>

                            <p>{booking.purpose || "Цель не указана"}</p>

                            <span className="status-badge">
                                {booking.status === "confirmed" ? "подтв." : booking.status}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default BookingCreate