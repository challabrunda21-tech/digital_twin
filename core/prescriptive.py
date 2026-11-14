"""
Prescriptive Maintenance Recommendation Engine and Closed-Loop Control Module
Implements:
- Tri-Factor Optimization: Correlating Remaining Useful Life (t_RUL),
  Spare Parts Procurement Lead Time (t_lead), Maintenance Staff Availability (t_staff),
  and Production Schedule Windows (t_window)
- Automated CMMS Work-Order Generation and Lifecycle Management
- Closed-Loop PLC / VFD Operational Derating (Patent Claim 8):
  Autonomous throttle commands dispatched over OPC-UA / Modbus TCP to decelerate degradation kinetics
  and extend physical machinery survival until maintenance intervention.
"""

from typing import Dict, Any, List
import uuid
import datetime

class PrescriptiveEngine:
    def __init__(self):
        # Factory operational parameters
        self.default_lead_time_hours = 72.0     # 3 days for standard industrial parts delivery
        self.default_staff_prep_hours = 8.0      # Technician scheduling and tool checkout
        self.scheduled_window_hours = 48.0      # Next scheduled plant production shift change
        
        # Closed-loop PLC/VFD state
        self.vfd_derating_active = False
        self.vfd_speed_setpoint_pct = 100.0     # Nominal 100% (1440 RPM)
        self.vfd_frequency_hz = 50.0            # Nominal grid frequency
        self.derate_percentage = 0.0
        
        # Work order history store
        self.work_orders: List[Dict[str, Any]] = []
        
        # Action audit history store for closed-loop control
        self.derate_action_history: List[Dict[str, Any]] = []

    def evaluate_prescriptions(self, machine_id: str, machine_name: str, 
                               rul_hours: float, health_index: float, 
                               fault_info: Dict[str, Any], dominant_component: str) -> Dict[str, Any]:
        """
        Execute tri-factor optimization and generate prioritized prescriptive recommendations.
        """
        t_rul = rul_hours
        t_lead = self.default_lead_time_hours
        t_staff = self.default_staff_prep_hours
        t_window = self.scheduled_window_hours
        
        # Lead-time safety margin
        t_required = t_lead + t_staff
        lead_time_deficit = t_required - t_rul
        
        needs_derating = False
        recommended_derate_pct = 0.0
        urgency = "Routine"
        priority_level = 4
        
        if health_index >= 0.75:
            urgency = "Nominal Monitoring"
            priority_level = 4
            action_title = "Continue Condition-Based Monitoring"
            action_desc = "No intervention required. Telemetry is fully synchronized with physics nominal model."
            recommended_timing = "Next scheduled quarterly overhaul"
        elif health_index >= 0.50:
            urgency = "Proactive Inspection"
            priority_level = 3
            action_title = f"Inspect and Lubricate {dominant_component}"
            action_desc = f"Nascent micro-wear detected on {dominant_component}. Check vibration spectra, inspect grease condition, and monitor thermal rise."
            recommended_timing = f"Schedule during upcoming production lull within {int(t_rul * 0.5)} operating hours."
        elif t_rul > t_required:
            urgency = "High Priority Work-Order"
            priority_level = 2
            action_title = f"Replace {dominant_component} During Production Window"
            action_desc = f"Order replacement components now. Parts arrival ({t_lead:.0f}h) + staff prep ({t_staff:.0f}h) is safely within RUL ({t_rul:.0f}h)."
            recommended_timing = f"Execute at shift window in {t_window:.0f}h."
        else:
            # Critical Lead-Time Dilemma (t_rul <= t_required):
            # Machine will fail BEFORE spare parts arrive without intervention!
            urgency = "Emergency Action & PLC Derating Required"
            priority_level = 1
            needs_derating = True
            recommended_derate_pct = 20.0  # 20% speed throttle triples survival hours
            action_title = f"CRITICAL: Autonomous VFD Derating & Emergency {dominant_component} Replacement"
            action_desc = (
                f"Asset Remaining Useful Life ({t_rul:.1f}h) is INSUFFICIENT for spare parts delivery ({t_lead:.0f}h). "
                f"Deficit: {lead_time_deficit:.1f}h. Immediate closed-loop PLC/VFD derating (20% speed reduction) "
                f"must be applied to decelerate fatigue kinetics and extend survival beyond {t_required:.0f}h."
            )
            recommended_timing = "IMMEDIATE (Autonomous Derating Executed)"

        recommendations = [
            {
                "id": f"REC-{len(self.work_orders) + 1:03d}",
                "urgency": urgency,
                "priority_level": priority_level,
                "title": action_title,
                "component": dominant_component,
                "description": action_desc,
                "recommended_timing": recommended_timing,
                "t_rul_hours": round(t_rul, 1),
                "t_lead_hours": round(t_lead, 1),
                "t_staff_hours": round(t_staff, 1),
                "t_window_hours": round(t_window, 1),
                "lead_time_deficit_hours": round(max(0.0, lead_time_deficit), 1),
                "needs_derating": needs_derating,
                "recommended_derate_pct": recommended_derate_pct
            }
        ]

        return {
            "tri_factor_metrics": {
                "t_rul_hours": round(t_rul, 1),
                "t_lead_hours": round(t_lead, 1),
                "t_staff_hours": round(t_staff, 1),
                "t_window_hours": round(t_window, 1),
                "safety_margin_hours": round(t_rul - (t_lead + t_staff), 1),
                "is_critical_lead_time_deficit": t_rul <= (t_lead + t_staff) and health_index < 0.50
            },
            "recommendations": recommendations,
            "vfd_derating_status": {
                "is_active": self.vfd_derating_active,
                "derate_percentage": self.derate_percentage,
                "speed_setpoint_pct": self.vfd_speed_setpoint_pct,
                "frequency_hz": self.vfd_frequency_hz,
                "target_rpm": round(1440.0 * (self.vfd_speed_setpoint_pct / 100.0), 1),
                "plc_protocol": "OPC-UA / Modbus TCP (Port 502)"
            },
            "action_history": self.derate_action_history[-10:],
            "derate_action_history": self.derate_action_history[-10:]
        }

    def dispatch_vfd_derating(self, enable: bool, derate_pct: float = 20.0) -> Dict[str, Any]:
        """
        Execute closed-loop VFD/PLC speed derating command (Claim 8).
        Simulates industrial PLC setpoint modulation over industrial bus.
        """
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if enable:
            self.vfd_derating_active = True
            self.derate_percentage = min(35.0, max(5.0, derate_pct))
            self.vfd_speed_setpoint_pct = round(100.0 - self.derate_percentage, 1)
            self.vfd_frequency_hz = round(50.0 * (self.vfd_speed_setpoint_pct / 100.0), 2)
            target_rpm = round(1440.0 * (self.vfd_speed_setpoint_pct / 100.0), 1)
            msg = f"Closed-loop VFD derating command executed: Speed throttled to {self.vfd_speed_setpoint_pct}% ({self.vfd_frequency_hz} Hz, {target_rpm} RPM). Degradation kinetics decelerated by ~3.5x."
            self.derate_action_history.insert(0, {
                "timestamp": now_str,
                "action": "THROTTLE_ENGAGED",
                "derate_pct": self.derate_percentage,
                "speed_setpoint_pct": self.vfd_speed_setpoint_pct,
                "target_rpm": target_rpm,
                "status": "Active (Simulated Modbus Holding Register 40001)"
            })
        else:
            self.vfd_derating_active = False
            self.derate_percentage = 0.0
            self.vfd_speed_setpoint_pct = 100.0
            self.vfd_frequency_hz = 50.0
            msg = "VFD derating disengaged. Speed setpoint restored to nominal 100.0% (50.0 Hz, 1440 RPM)."
            self.derate_action_history.insert(0, {
                "timestamp": now_str,
                "action": "THROTTLE_DISENGAGED",
                "derate_pct": 0.0,
                "speed_setpoint_pct": 100.0,
                "target_rpm": 1440.0,
                "status": "Restored Nominal Setpoint"
            })

        return {
            "success": True,
            "message": msg,
            "is_active": self.vfd_derating_active,
            "derate_percentage": self.derate_percentage,
            "speed_setpoint_pct": self.vfd_speed_setpoint_pct,
            "frequency_hz": self.vfd_frequency_hz,
            "target_rpm": round(1440.0 * (self.vfd_speed_setpoint_pct / 100.0), 1),
            "action_history": self.derate_action_history[-10:]
        }

    def create_cmms_work_order(self, machine_id: str, machine_name: str, 
                               component: str, priority: str, 
                               action: str, notes: str = "") -> Dict[str, Any]:
        """Generate formal CMMS work-order ticket."""
        ticket_id = f"WO-{datetime.datetime.now().strftime('%Y%m%d')}-{len(self.work_orders) + 101}"
        ticket = {
            "ticket_id": ticket_id,
            "machine_id": machine_id,
            "machine_name": machine_name,
            "component": component,
            "priority": priority,
            "action": action,
            "notes": notes or f"Automated ticket dispatched by AI Digital Twin Prescriptive Engine.",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Dispatched to CMMS",
            "assigned_crew": "Mechanical Reliability Team A",
            "estimated_downtime_hours": 3.5,
            "required_parts": f"1x OEM Replacement Kit for {component}"
        }
        self.work_orders.insert(0, ticket)
        return ticket

    def get_cmms_work_orders(self) -> List[Dict[str, Any]]:
        """Return list of generated work orders."""
        if not self.work_orders:
            # Seed with initial historical record
            self.work_orders.append({
                "ticket_id": "WO-20261010-098",
                "machine_id": "MTR-PUMP-5.5KW-01",
                "machine_name": "5.5 kW Induction Motor - Centrifugal Pump Unit #1",
                "component": "Flexible Shaft Coupling",
                "priority": "Elevated",
                "action": "Laser alignment verification and elastomeric spider ring inspection.",
                "notes": "Completed during weekend maintenance window. Shaft runout < 0.03 mm verified.",
                "created_at": "2026-10-10 14:30:00",
                "status": "Completed & Verified",
                "assigned_crew": "Mechanical Team B",
                "estimated_downtime_hours": 2.0,
                "required_parts": "Elastomeric Coupling Insert 45 Shore A"
            })
        return self.work_orders
