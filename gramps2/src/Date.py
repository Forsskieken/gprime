#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"Support for dates"

__author__ = "Donald N. Allingham"
__version__ = "$Revision$"

#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
from re import IGNORECASE, compile
import string
import time

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import Calendar
from intl import gettext as _

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
UNDEF = -999999

_calendar_val = [
    Calendar.Gregorian,
    Calendar.Julian,
    Calendar.Hebrew,
    Calendar.FrenchRepublic,
    ]

#-------------------------------------------------------------------------
#
# Date class
#
#-------------------------------------------------------------------------
class Date:
    """
    The core date handling class for GRAMPs. Supports partial dates,
    date ranges, and alternate calendars.
    """
    formatCode = 0
    
    Error = "Illegal Date"

    fstr = _("(from|between|bet|bet.)")
    tstr = _("(and|to|-)")
    
    fmt = compile("\s*%s\s+(.+)\s+%s\s+(.+)\s*$" % (fstr,tstr),IGNORECASE)

    def __init__(self,source=None):
        if source:
            self.start = SingleDate(source.start)
            if source.stop:
                self.stop = SingleDate(source.stop)
            else:
                self.stop = None
            self.range = source.range
            self.text = source.text
            self.calendar = source.calendar
        else:
            self.start = SingleDate()
            self.stop = None
            self.range = 0
            self.text = ""
            self.calendar = Calendar.Gregorian()

    def get_calendar(self):
        return self.calendar

    def set_calendar(self,val):
        self.calendar = val()
        self.start.convert_to(val)
        if self.stop:
            self.stop.convert_to(val)

    def set_calendar_obj(self,val):
        self.calendar = val
        self.start.convert_to_obj(val)
        if self.stop:
            self.stop.convert_to_obj(val)

    def set_calendar_val(self,integer):
        val = _calendar_val[integer]
        self.calendar = val()
        self.start.convert_to(val)
        if self.stop:
            self.stop.convert_to(val)

    def get_start_date(self):
        return self.start

    def get_stop_date(self):
        if self.stop == None:
            self.stop = SingleDate()
            self.stop.calendar = self.calendar
        return self.stop

    def getLowYear(self):
        return self.start.getYear()
        
    def getHighYear(self):
        if self.stop == None:
            return self.start.getYear()
        else:
            return self.stop.getYear()

    def getYear(self):
        return self.start.year

    def getYearValid(self):
        return self.start.year != UNDEF

    def getMonth(self):
        if self.start.month == UNDEF:
            return UNDEF
        return self.start.month+1

    def getMonthValid(self):
        return self.start.month != UNDEF

    def getDay(self):
        return self.start.day

    def getDayValid(self):
        return self.start.day != UNDEF

    def getValid(self):
        """ Returns true if any part of the date is valid"""
        return self.start.year != UNDEF or self.start.month != UNDEF or self.start.day != UNDEF

    def getIncomplete(self):
        return self.range == 0 and self.start.year == UNDEF or \
               self.start.month == UNDEF or self.start.day == UNDEF

    def getStopYear(self):
        if self.stop == None:
            self.stop = SingleDate()
            self.stop.calendar = self.calendar
        return self.stop.year

    def getStopMonth(self):
        if self.stop == None:
            self.stop = SingleDate()
            self.stop.calendar = self.calendar
        return self.stop.month+1

    def getStopDay(self):
        if self.stop == None:
            self.stop = SingleDate()
            self.stop.calendar = self.calendar
        return self.stop.day

    def getText(self):
        return self.text

    def greater_than(self,other):
        return compare_dates(self,other) > 0

    def less_than(self,other):
        return compare_dates(self,other) < 0

    def equal_to(self,other):
        return compare_dates(self,other) == 0

    def set(self,text):
        match = Date.fmt.match(text)
        try:
            if match:
                matches = match.groups()
                self.start.set(matches[1])
                if self.stop == None:
                    self.stop = SingleDate()
                self.stop.calendar = self.calendar
                self.stop.set(matches[3])
                self.range = 1
            else:
                self.start.set(text)
                self.range = 0
        except Date.Error:
            if text != "":
                self.range = -1
            self.text = text

    def set_text(self,text):
        self.range = -1
        self.text = text

    def set_range(self,val):
        self.range = val
    
    def getDate(self):
        if self.range == 0:
            return self.start.getDate()
        elif self.range == -1:
            return "%s" % self.text
        else:
            return _("from %(start_date)s to %(stop_date)s") % {
                'start_date' : self.start.getDate(),
                'stop_date' : self.stop.getDate() }

    def getQuoteDate(self):
        if self.range == 0:
            return self.start.getQuoteDate()
        elif self.range == -1:
            if self.text:
                return '"%s"' % self.text
            else:
                return ''
        else:
            return _("from %(start_date)s to %(stop_date)s") % {
                'start_date' : self.start.getQuoteDate(),
                'stop_date' : self.stop.getQuoteDate() }

    def isEmpty(self):
        s = self.start
        return s.year==UNDEF and s.month==UNDEF and s.day==UNDEF and not self.text

    def isValid(self):
        return self.range != -1 

    def isRange(self):
        return self.range == 1
        
#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def set_format_code(code):
    global _func
    Date.formatCode = code
    _func = SingleDate.fmtFunc[code]

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def get_format_code():
    return Date.formatCode

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
class SingleDate:
    "Date handling"

    def __init__(self,source=None):
        if source:
            self.month = source.month
            self.day = source.day
            self.year = source.year
            self.mode = source.mode
            self.calendar = source.calendar
        else:
            self.month = UNDEF
            self.day = UNDEF
            self.year = UNDEF
            self.mode = Calendar.EXACT
            self.calendar = Calendar.Gregorian()

    def setMode(self,val):
        self.mode = self.calendar.set_mode_value(val)

    def setMonth(self,val):
        if val > 14 or val < 0:
            self.month = UNDEF
        else:
            self.month = val

    def setMonthVal(self,s):
        self.month = self.calendar.set_value(s)

    def setDayVal(self,s):
        self.day = self.calendar.set_value(s)

    def setYearVal(self,s):
        if s:
            self.year = self.calendar.set_value(s)
        else:
            self.year = UNDEF

    def getMonth(self):
        return self.month

    def getMonthValid(self):
        return self.month != UNDEF

    def setDay(self,val):
        self.day = val

    def getDay(self):
	return self.day

    def getDayValid(self):
	return self.day != UNDEF

    def setYear(self,val):
        self.year = val

    def getYear(self):
        return self.year

    def getYearValid(self):
        return self.year != UNDEF

    def getValid(self):
        """ Returns true if any part of the date is valid"""
        return self.year != UNDEF or self.month != UNDEF or self.day != UNDEF

    def setMonthStr(self,text):
        self.calendar.set_month_string(text)

    def getMonthStr(self):
	return _mname[self.month]

    def getIsoDate(self):
        if self.year == UNDEF:
            y = "????"
        else:
            y = "%04d" % self.year
        if self.month == UNDEF:
            if self.day == UNDEF:
                m = ""
            else:
                m = "-??"
        else:
            m = "-%02d" % (self.month+1)
        if self.day == UNDEF:
            d = ''
        else:
            d = "-%02d" % self.day
        return "%s%s%s" % (y,m,d)
        
    def _format1(self):
        if self.month == UNDEF and self.day == UNDEF and self.year == UNDEF:
            return ""
        elif self.day == UNDEF:
            if self.month == UNDEF:
                retval = str(self.year)
            elif self.year == UNDEF:
                retval = _mname[self.month]
            else:
                try:
                    retval = "%s %d" % (_mname[self.month],self.year)
                except:
                    retval = "**** %d %d %d ****" % (self.year,self.month,self.day)
        elif self.month == UNDEF:
            retval = str(self.year)
        else:
            try:
                month = _mname[self.month]
            except:
                month = "<ILLEGAL MONTH>"
            if self.year == UNDEF:
                retval = "%s %d, ????" % (month,self.day)
            else:
                retval = "%s %d, %d" % (month,self.day,self.year)

        if self.mode == Calendar.ABOUT:
	    retval = _("about") + ' ' + retval
        elif self.mode == Calendar.BEFORE:
            retval = _("before") + ' ' + retval
        elif self.mode == Calendar.AFTER:
            retval = _("after") + ' ' + retval
        return retval

    def _format2(self):
        if self.month == UNDEF and self.day == UNDEF and self.year == UNDEF :
            return ""
        elif self.month != UNDEF and self.month != UNDEF:
            month = _mname[self.month]
            if self.year == UNDEF:
                retval = "%s %d, ????" % (string.upper(month[0:3]),self.day)
            else:
                retval = "%s %d, %d" % (string.upper(month[0:3]),self.day,self.year)
        elif self.day == UNDEF:
            if self.month == UNDEF:
                retval = str(self.year)
            elif self.year == UNDEF:
                month = _mname[self.month]
                retval = string.upper(month[0:3])
            else:	
                month = _mname[self.month]
                retval = "%s %d" % (string.upper(month[0:3]),self.year)
        else:
            retval =  str(self.year)

        if self.mode == Calendar.ABOUT:
            retval = "%s %s" % (_("abt"),retval)
        elif self.mode == Calendar.BEFORE:
            retval = "%s %s" % (_("before"),retval)
        elif self.mode == Calendar.AFTER:
            retval = "%s %s" % (_("after"),retval)

        return retval

    def _format3(self):
        if self.month == UNDEF and self.day == UNDEF and self.year == UNDEF :
            return ""
        elif self.day == UNDEF:
            if self.month == UNDEF:
                retval = str(self.year)
            elif self.year == UNDEF:
                month = _mname[self.month]
                retval = string.upper(month[0:3])
            else:
                month = _mname[self.month]
                retval = "%s %d" % (string.upper(month[0:3]),self.year)
        elif self.month == UNDEF:
            retval = str(self.year)
        else:
            month = _mname[self.month]
            if self.year == UNDEF:
                retval = "%d %s ????" % (self.day,string.upper(month[0:3]))
            else:
                retval = "%d %s %d" % (self.day,string.upper(month[0:3]),self.year)

        if self.mode == Calendar.ABOUT:
            retval = "%s %s" % (_("ABOUT"),retval)
        elif self.mode == Calendar.BEFORE:
            retval = "%s %s" % (_("BEFORE"),retval)
        elif self.mode == Calendar.AFTER:
            retval = "%s %s" % (_("AFTER"),retval)
        return retval

    def _format10(self):
        if self.month == UNDEF and self.day == UNDEF and self.year == UNDEF :
            return ""
        elif self.day == UNDEF:
            if self.month == UNDEF:
                retval = str(self.year)
            elif self.year == UNDEF:
                retval = _mname[self.month]
            else:
                month = _mname[self.month]
                retval = "%s %d" % (month,self.year)
        elif self.month == UNDEF:
            retval = str(self.year)
        else:
            month = _mname[self.month]
            if self.year == UNDEF:
                retval = "%d. %s ????" % (self.day,month)
            else:
                retval = "%d. %s %d" % (self.day,month,self.year)

        if self.mode == Calendar.ABOUT:
            retval = "%s %s" % (_("ABOUT"),retval)
        elif self.mode == Calendar.BEFORE:
            retval = "%s %s" % (_("BEFORE"),retval)
        elif self.mode == Calendar.AFTER:
            retval = "%s %s" % (_("AFTER"),retval)

        return retval

    def _get_mmddyyyy(self,sep):
        if self.month == UNDEF and self.day == UNDEF and self.year == UNDEF :
            return ""
        elif self.day == UNDEF:
            if self.month == UNDEF:
                retval = str(self.year)
            elif self.year == UNDEF:
                retval = "%02d%s??%s??" % (self.month+1,sep,sep)
            else:
                retval = "%02d%s??%s%04d" % (self.month+1,sep,sep,self.year)
        elif self.month == UNDEF:
            retval = "??%s%02d%s%04d" % (sep,self.day,sep,self.year)
        else:
            if self.year == UNDEF:
                retval = "%02d%s%02d%s????" % (self.month+1,sep,self.day,sep)
            else:
                retval = "%02d%s%02d%s%04d" % (self.month+1,sep,self.day,sep,self.year)

        if self.mode == Calendar.ABOUT:
            retval = "%s %s" % (_("ABOUT"),retval)
        elif self.mode == Calendar.BEFORE:
            retval = "%s %s" % (_("BEFORE"),retval)
        elif self.mode == Calendar.AFTER:
            retval = "%s %s" % (_("AFTER"),retval)

        return retval

    def _get_yyyymmdd(self,sep):
        retval = ""
        
        if self.month == UNDEF and self.day == UNDEF and self.year == UNDEF :
            pass
        elif self.day == UNDEF:
            if self.month == UNDEF:
                retval = str(self.year)
            elif self.year == UNDEF:
                retval = "????%s%02d%s??" % (sep,self.month+1,sep)
            else:
                retval = "%04d%s%02d" % (self.year,sep,self.month+1)
        elif self.month == UNDEF:
            retval = "%04d%s??%s%02d" % (self.year,sep,sep,self.day)
        else:
            if self.year == UNDEF:
                retval = "????%s%02d%s%02d" % (sep,self.month+1,sep,self.day)
            else:
                retval = "%02d%s%02d%s%02d" % (self.year,sep,self.month+1,sep,self.day)

        if self.mode == Calendar.ABOUT:
            retval = "%s %s" % (_("about"),retval)

        if self.mode == Calendar.BEFORE:
            retval = "%s %s" % (_("before"),retval)
        elif self.mode == Calendar.AFTER:
            retval = "%s %s" % (_("after"),retval)

        return retval

    def _format4(self):
        return self._get_mmddyyyy("/")

    def _format5(self):
        return self._get_mmddyyyy("-")

    def _format8(self):
        return self._get_mmddyyyy(".")

    def _get_ddmmyyyy(self,sep):
        retval = ""
        
        if self.month == UNDEF and self.day == UNDEF and self.year == UNDEF :
            pass
        elif self.day == UNDEF:
            if self.month == UNDEF:
                retval = str(self.year)
            elif self.year == UNDEF:
                retval = "??%s%02d%s??" % (sep,self.month+1,sep)
            else:
                retval = "??%s%02d%s%04d" % (sep,self.month+1,sep,self.year)
        elif self.month == UNDEF:
            retval = "%02d%s??%s%04d" % (self.day,sep,sep,self.year)
        else:
            if self.year == UNDEF:
                retval = "%02d%s%02d%s????" % (self.day,sep,self.month+1,sep)
            else:
                retval = "%02d%s%02d%s%04d" % (self.day,sep,self.month+1,sep,self.year)

        if self.mode == Calendar.ABOUT:
            retval = "%s %s" % (_("ABOUT"),retval)
        if self.mode == Calendar.BEFORE:
            retval = "%s %s" % (_("BEFORE"),retval)
        elif self.mode == Calendar.AFTER:
            retval = "%s %s" % (_("AFTER"),retval)

        return retval

    def _format6(self):
        return self._get_ddmmyyyy("/")

    def _format7(self):
        return self._get_ddmmyyyy("-")

    def _format9(self):
        return self._get_ddmmyyyy(".")

    def _format11(self):
        return self._get_yyyymmdd("/")

    def _format12(self):
        return self._get_yyyymmdd("-")

    def _format13(self):
        return self._get_yyyymmdd(".")

    #--------------------------------------------------------------------
    #
    # 
    #
    #--------------------------------------------------------------------
    fmtFunc = [ _format1, _format2, _format3, _format4, _format5, _format6,
                _format7, _format8, _format9, _format10, _format11, _format12,
                _format13]

    def getDate(self):
        return self.calendar.display(self.year, self.month, self.day, self.mode)

    def getQuoteDate(self):
        if self.year == UNDEF and self.month == UNDEF and self.day == UNDEF:
            return ""
        else:
            return self.calendar.quote_display(self.year, self.month, self.day, self.mode)

    def setIsoDate(self,v):
        data = string.split(v)
        if len(data) > 1:
            self.setMode(data[0])
            v = data[1]
        
        vals = string.split(v,'-')
        self.setYearVal(vals[0])
        if len(vals) > 1:
            self.setMonthVal(int(vals[1])-1)
        else:
            self.month = UNDEF
        if len(vals) > 2:
            self.setDayVal(vals[2])
        else:
            self.day = UNDEF
        
    def getModeVal(self):
        return self.mode

    def setModeVal(self,val):
        self.mode = val
    
    def set(self,text):
        self.year, self.month, self.day, self.mode = self.calendar.set(text)
        
    def convert_to(self,val):
        sdn = self.calendar.get_sdn(self.year, self.month, self.day)
        self.calendar = val()
        (self.year, self.month, self.day) = self.calendar.get_ymd(sdn)

    def convert_to_obj(self,val):
        sdn = self.calendar.get_sdn(self.year, self.month, self.day)
        self.calendar = val
        (self.year, self.month, self.day) = self.calendar.get_ymd(sdn)

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def not_too_old(date):
    time_struct = time.localtime(time.time())
    current_year = time_struct[0]
    if date.year != UNDEF and current_year - date.year > 110:
        return 0
    return 1

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
def compare_dates(f,s):
    if f.calendar.NAME != s.calendar.NAME:
        return 1
    if f.range == -1 and s.range == -1:
        return cmp(f.text,s.text)
    if f.range == -1 or s.range == -1:
        return -1
    
    first = f.get_start_date()
    second = s.get_start_date()
    if first.year != second.year:
        return cmp(first.year,second.year)
    elif first.month != second.month:
        return cmp(first.month,second.month)
    elif f.range != 1:
        return cmp(first.day,second.day)
    else:
        first = f.get_stop_date()
        second = s.get_stop_date()
        if first.year != second.year:
            return cmp(first.year,second.year)
        elif first.month != second.month:
            return cmp(first.month,second.month)
        else:
            return cmp(first.day,second.day)
            
_func = SingleDate.fmtFunc[0]


if __name__ == "__main__":

    a = Date()
    a.set("24 May 1961")
    print "Gregorian : ", a.getDate()
    a.set(a.getDate())
    print "Gregorian : ", a.getDate()

    a.set_calendar(Calendar.Julian)
    print "Julian : ", a.getDate()
    a.set(a.getDate())
    print "Julian : ", a.getDate()

    a.set_calendar(Calendar.Gregorian)
    print "Gregorian : ", a.getDate()
    a.set(a.getDate())
    print "Gregorian : ", a.getDate()

    a.set_calendar(Calendar.Hebrew)
    print "Hebrew : ", a.getDate()
    a.set(a.getDate())
    print "Hebrew : ", a.getDate()

    a.set_calendar(Calendar.Gregorian)
    print "Gregorian : ", a.getDate()
    a.set(a.getDate())
    print "Gregorian : ", a.getDate()

    a.set_calendar(Calendar.Persian)
    print "Persian : ", a.getDate()
    a.set(a.getDate())
    print "Persian : ", a.getDate()

    a.set_calendar(Calendar.Gregorian)
    print "Gregorian : ", a.getDate()
    a.set(a.getDate())
    print "Gregorian : ", a.getDate()

    a.set_calendar(Calendar.Islamic)
    print "Islamic : ", a.getDate()
    a.set(a.getDate())
    print "Islamic : ", a.getDate()

    a.set_calendar(Calendar.Gregorian)
    print "Gregorian : ", a.getDate()
    a.set(a.getDate())
    print "Gregorian : ", a.getDate()

