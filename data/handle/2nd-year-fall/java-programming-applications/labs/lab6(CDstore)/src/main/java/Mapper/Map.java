package Mapper;


import Bean.Disk;
import Bean.User;
import Bean.storeDisk;
import Bean.storeUser;

public class Map {
	private storeDisk sDisk;
	private storeUser sUser;
	
	public Map() {
		sDisk=new storeDisk();
		sUser=new storeUser();
	}
	
	public storeDisk getsDisk() {
		return sDisk;
	}
	public storeUser getsUser() {
		return sUser;
	}
	
	public void addDisk(Disk d) {
	
		for (var iterator =sDisk.iterator(); iterator.hasNext();) {
			Disk disk = (Disk) iterator.next();
			if(d.equals(disk)) {
				disk.setMoney(d.getMoney());
				disk.setNum(d.getNum());
				return;
			}
		}
		sDisk.add(d);
	}
	
	public void addUser(User u) {
		for (var iterator =sUser.iterator(); iterator.hasNext();) {
			User user = (User) iterator.next();
			if(u.equals(user)) {System.out.println("User Deplicated");
				return;
			
			}
		}
		sUser.add(u);
	}
	
	public void delUser(User u) {
		if(sUser.remove(u)==false) {
			System.out.println("Delete Failed");
		}
		
	}
	
	// private void delDisk() {
		

	// }
	
	public void reportStore() {
		System.out.println(sDisk.toString());
		
	}
	
	public void reportUser() {
		System.out.println(sUser.toString());
		
	}

	public boolean rent(User rent) {
		
		for (var iteratorUser =sUser.iterator(); iteratorUser.hasNext();) {
			User user = (User) iteratorUser.next();
			if(user.equals(rent)) {
				for (var iteratorDisk =sDisk.iterator(); iteratorDisk.hasNext();) {
					Disk disk = (Disk) iteratorDisk.next();
					if(rent.getBorrowed().getLast().equals(disk)) {
						Disk torentDisk=rent.getBorrowed().getLast();
						torentDisk.setMoney(disk.getMoney());
						if(user.getMoney()>=torentDisk.getMoney()*torentDisk.getNum()&&torentDisk.getNum()<=disk.getNum()) {
							user.setBorrowed(torentDisk);
							user.setMoney(user.getMoney()-torentDisk.getMoney()*torentDisk.getNum());
							disk.setNum(disk.getNum()-torentDisk.getNum());
							return true;
						}else {
							System.out.println("No Money or No Enough Quantity!");
							return false;
						}
					}
				}
				System.out.println("No this disk!");
				return false;
				
			}
		}
		System.out.println("User not Found!");
		return false;
		
	}

	public boolean buy(User buy) {
		for (var iteratorUser =sUser.iterator(); iteratorUser.hasNext();) {
			User user = (User) iteratorUser.next();
			if(user.equals(buy)) {
				for (var iteratorDisk =sDisk.iterator(); iteratorDisk.hasNext();) {
					Disk disk = (Disk) iteratorDisk.next();
					if(buy.getBorrowed().getLast().equals(disk)) {
						Disk tobuyDisk=buy.getBorrowed().getLast();
						tobuyDisk.setMoney(disk.getMoney());
						if(user.getMoney()>=tobuyDisk.getMoney()*tobuyDisk.getNum()&&tobuyDisk.getNum()<=disk.getNum()) {
							user.setMoney(user.getMoney()-tobuyDisk.getMoney()*tobuyDisk.getNum());
							disk.setNum(disk.getNum()-tobuyDisk.getNum());
							return true;
						}else {
							System.out.println("No Money or No Enough Quantity!");
							return false;
						}
					}
				
				}
				System.out.println("No this disk!");
				return false;
			}
		}
		System.out.println("User not Found!");
		return false;
	}

	
}
