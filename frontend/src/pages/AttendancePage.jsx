import { useState, useEffect } from 'react';
import { Calendar, Users, CheckCircle, Search, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { API_URL, formatDate, formatNumber } from '@/lib/utils';
import { safeImgSrc } from '@/utils/sanitize';

export default function AttendancePage() {
  const [services, setServices] = useState([]);
  const [serviceTypes, setServiceTypes] = useState([]);
  const [selectedService, setSelectedService] = useState(null);
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [servicesRes, typesRes] = await Promise.all([
        fetch(`${API_URL}/services?limit=20`),
        fetch(`${API_URL}/service-types`),
      ]);

      const [servicesData, typesData] = await Promise.all([
        servicesRes.json(),
        typesRes.json(),
      ]);

      setServices(servicesData);
      setServiceTypes(typesData);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadServiceAttendance = async (serviceId) => {
    try {
      const response = await fetch(`${API_URL}/attendance/service/${serviceId}`);
      const data = await response.json();
      setAttendance(data);
    } catch (error) {
      console.error('Failed to fetch attendance:', error);
    }
  };

  const handleServiceSelect = (service) => {
    setSelectedService(service);
    loadServiceAttendance(service.id);
  };

  // Group services by date
  const groupedServices = services.reduce((acc, service) => {
    const date = service.date;
    if (!acc[date]) acc[date] = [];
    acc[date].push(service);
    return acc;
  }, {});

  return (
    <div className="space-y-6 animate-fade-in" data-testid="attendance-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Attendance</h1>
          <p className="page-subtitle">Track service and group attendance</p>
        </div>
        <Button className="h-9 btn-primary" data-testid="record-attendance-btn">
          <Plus className="w-4 h-4 mr-2" />
          Record Attendance
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">This Week</p>
          <p className="text-2xl font-bold font-data text-slate-900">
            {services[0]?.total_headcount ? formatNumber(services[0].total_headcount) : '—'}
          </p>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Last Week</p>
          <p className="text-2xl font-bold font-data text-slate-900">
            {services[2]?.total_headcount ? formatNumber(services[2].total_headcount) : '—'}
          </p>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Avg (4 weeks)</p>
          <p className="text-2xl font-bold font-data text-slate-900">
            {formatNumber(Math.round(services.slice(0, 8).reduce((acc, s) => acc + (s.total_headcount || 0), 0) / 4))}
          </p>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Service Types</p>
          <p className="text-2xl font-bold font-data text-slate-900">{serviceTypes.length}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Services List */}
        <div className="lg:col-span-1 bg-white border border-slate-200 rounded-lg">
          <div className="p-4 border-b border-slate-200">
            <h3 className="font-semibold text-slate-900">Recent Services</h3>
          </div>
          <div className="max-h-[600px] overflow-y-auto">
            {loading ? (
              <div className="p-4 space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-16 bg-slate-100 rounded animate-pulse"></div>
                ))}
              </div>
            ) : (
              Object.entries(groupedServices).map(([date, dateServices]) => (
                <div key={date} className="border-b border-slate-100 last:border-0">
                  <div className="px-4 py-2 bg-slate-50 text-xs font-medium text-slate-500">
                    {formatDate(date)}
                  </div>
                  {dateServices.map((service) => (
                    <button
                      key={service.id}
                      className={`w-full p-4 text-left hover:bg-slate-50 transition-colors ${
                        selectedService?.id === service.id ? 'bg-blue-50 border-l-2 border-l-blue-600' : ''
                      }`}
                      onClick={() => handleServiceSelect(service)}
                      data-testid={`service-${service.id}`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-slate-900">{service.service_type_name}</p>
                          <p className="text-sm text-slate-500">{service.time || 'Time not set'}</p>
                        </div>
                        {service.total_headcount && (
                          <span className="text-lg font-bold font-data text-slate-900">
                            {formatNumber(service.total_headcount)}
                          </span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Attendance Detail */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-lg">
          {!selectedService ? (
            <div className="h-full flex items-center justify-center py-20">
              <div className="text-center">
                <Calendar className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                <h3 className="font-semibold text-slate-900 mb-2">Select a Service</h3>
                <p className="text-slate-400 text-sm">Choose a service from the list to view attendance</p>
              </div>
            </div>
          ) : (
            <>
              <div className="p-4 border-b border-slate-200 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900">
                    {selectedService.service_type_name} - {formatDate(selectedService.date)}
                  </h3>
                  <p className="text-sm text-slate-500">{attendance.length} checked in</p>
                </div>
                <Button size="sm" data-testid="add-attendance-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Check In
                </Button>
              </div>
              <div className="p-4">
                <div className="relative mb-4">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input placeholder="Search attendees..." className="pl-9" />
                </div>
                
                {attendance.length === 0 ? (
                  <div className="text-center py-12 text-slate-400">
                    No attendance records for this service
                  </div>
                ) : (
                  <div className="space-y-2">
                    {attendance.map((record) => (
                      <div 
                        key={record.id}
                        className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          {record.photo_url ? (
                            <img src={safeImgSrc(record.photo_url)} alt="" className="w-10 h-10 rounded-full" />
                          ) : (
                            <div className="w-10 h-10 rounded-full bg-slate-200 flex items-center justify-center">
                              <Users className="w-5 h-5 text-slate-400" />
                            </div>
                          )}
                          <div>
                            <p className="font-medium text-slate-900">
                              {record.first_name} {record.last_name}
                            </p>
                            <p className="text-xs text-slate-500">
                              Checked in at {new Date(record.check_in_time).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                        <CheckCircle className="w-5 h-5 text-emerald-500" />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
